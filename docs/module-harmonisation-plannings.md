# Support technique — Module Harmonisation des plannings

> Terminologie : **"harmonisation"** est le terme utilisé côté interface (pages,
> libellés). Côté code, le même concept s'appelle **"alignement"**
> (`alignement_service.py`, `PropositionAlignement`, `type_alignement`...).
> Les deux mots désignent exactement la même chose dans ce document.

Document vivant : à mettre à jour à chaque modification du module (voir
[Journal des modifications](#journal-des-modifications) en fin de fichier).

---

## Sommaire

1. [Objectif métier](#1-objectif-métier)
2. [Vue d'ensemble du flux](#2-vue-densemble-du-flux)
3. [Algorithme de détection et de génération](#3-algorithme-de-détection-et-de-génération)
4. [Modèle de données](#4-modèle-de-données)
5. [Endpoints API](#5-endpoints-api)
6. [Cycle de vie d'une proposition](#6-cycle-de-vie-dune-proposition)
7. [Application et refus — effets exacts](#7-application-et-refus--effets-exacts)
8. [Consommation frontend](#8-consommation-frontend)
9. [Points critiques connus](#9-points-critiques-connus)
10. [Journal des modifications](#journal-des-modifications)

---

## 1. Objectif métier

Quand deux travaux de maintenance (souvent de plannings, voire d'entités
métier différentes — Transport / Distribution / Production) portent sur une
ressource électrique commune (poste, rame, départ) et que leurs périodes se
chevauchent, le système :

1. **détecte** le conflit ;
2. **propose** de recaler le travail le moins prioritaire sur la fenêtre du
   plus prioritaire, pour que les deux équipes interviennent pendant la même
   indisponibilité au lieu de deux coupures séparées ;
3. laisse un **gestionnaire de planification** accepter ou refuser cette
   proposition.

## 2. Vue d'ensemble du flux

```
Gestionnaire clique "Analyser" (page Alertes, mois/année sélectionnés)
        │
        ▼
POST /plannings/analyser-mois/  ──────────────►  analyser_mois(user, annee, mois)
        │                                          (planning/alignement_service.py)
        ▼
   Détection des groupes de travaux en conflit
        │
        ▼
   Génération / réutilisation des PropositionAlignement
        │
        ▼
   Réponse : { chevauchements, propositions, resume }
        │
        ▼
Frontend (AlertesView, CalendarView, Dashboard/Alert) affiche les groupes
        │
        ▼
Gestionnaire ouvre un groupe → Gantt avancé → Appliquer / Refuser une proposition
        │                                              │
        ▼                                              ▼
POST .../appliquer-proposition/                POST .../refuser-proposition/
   → Travail replanifié                           → aucun changement sur le Travail
   → proposition.statut = ACCEPTEE                → proposition.statut = REFUSEE
```

Il n'existe **qu'un seul point d'entrée actif** pour la détection :
`analyser_mois`. Une fonction plus ancienne, `analyser_et_proposer`
(analyse limitée à un seul planning), a existé mais n'était plus appelée par
aucune vue — elle a été retirée du code le 2026-08-17 (dead code, voir
[Journal](#journal-des-modifications)).

## 3. Algorithme de détection et de génération

Fichier : [`planning/alignement_service.py`](../planning/alignement_service.py)

### 3.1 Périmètre analysé

`analyser_mois(user, annee, mois)` charge **tous les travaux, tous plannings
confondus**, dont la période touche le mois demandé :

```python
heure_debut_planifie <= fin_du_mois  ET  heure_fin_planifie >= debut_du_mois
```

Cela capture aussi les travaux qui débordent sur le mois précédent/suivant.
Un travail sans horaire planifié est ignoré.

### 3.2 Deux travaux sont-ils liés ? — `_partage_ressource`

Trois filtres cumulatifs :

| # | Condition | Résultat si non respectée |
|---|-----------|---------------------------|
| 1 | Aucun des deux n'est `PRODUCTION` | Production exclue de l'alignement (pour l'instant) |
| 2 | Même région électrique **et** même poste (déduits des `items` de la `Reference`) | Pas de lien |
| 3 | Compatibilité de niveau de coupure (voir ci-dessous) | Pas de lien |

Règles du niveau de coupure (`niveau_coupure`) :

- **Coupure poste** (ou segment `TRANSPORT`, qui coupe toujours au poste) ↔
  n'importe quoi sur ce poste → **compatible**.
- **Coupure rame** ↔ rame identique, ou départ appartenant à cette rame →
  **compatible**.
- **Coupure départ** ↔ exactement le même départ → **compatible**.
- Toute autre combinaison → **pas de lien**.

### 3.3 Chevauchement temporel — `_periodes_se_chevauchent`

`debut_a < fin_b ET fin_a > debut_b`. Un lien de ressource sans chevauchement
horaire ne produit rien.

### 3.4 Regroupement — `_detecter_groupes`

Union-find sur toutes les paires liées + chevauchantes : si A-B et B-C sont
liés, les trois forment **un seul groupe**, même si A et C n'ont aucun lien
direct (pour éviter qu'aligner B sur A ne recrée un conflit avec C). Seuls
les groupes d'au moins 2 travaux sont conservés.

> ⚠️ Un alignement réussi reste, par construction, un "chevauchement" : les
> deux travaux occupent désormais volontairement la même fenêtre. `analyser_mois`
> filtre donc, pour chaque groupe, les membres déplaçables déjà exactement
> calés sur la fenêtre du pivot (`heure_debut_planifie`/`heure_fin_planifie`
> == le calcul de `_calculer_nouvel_horaire` donnerait la même chose) : un
> groupe entièrement résolu de cette façon **disparaît de `chevauchements`**
> plutôt que de régénérer indéfiniment une proposition `EN_ATTENTE` no-op à
> chaque nouvelle analyse (correctif 2026-08-25, voir §9.9).

### 3.5 Choix du pivot — `_trouver_reference`

Dans chaque groupe, tri par : **TRANSPORT** > **alignement verrouillé** (2026-08-23,
§9.3) > **P1** > le plus tôt planifié > (à égalité) le plus long. Le pivot ne
bouge jamais ; tous les autres membres du groupe sont évalués contre lui.
Un travail dont l'alignement a été fixé manuellement par un gestionnaire
(`Travail.alignement_verrouille`) passe donc devant P1/P2/P3 pour devenir la
référence du groupe : les autres s'alignent sur sa décision plutôt que
l'inverse.

### 3.6 Génération d'une proposition pour chaque autre travail du groupe

1. **`_peut_bouger(travail)`** : `TRANSPORT` → jamais déplaçable ;
   `alignement_verrouille` → jamais déplaçable (2026-08-23, §9.3) ; `P1` →
   jamais déplaçable ; `P2`/`P3` → déplaçable.
   - Si `False` → proposition créée directement avec `statut = BLOQUEE`,
     `nouveau_debut = ancien_debut` (aucun déplacement calculé), résolution
     manuelle requise. `raison` précise laquelle des trois causes s'applique
     (`_raison_non_deplacable`).
2. Sinon, **`_calculer_nouvel_horaire(travail, reference)`** : cale le début
   du travail sur le début du pivot, **en conservant sa durée d'origine**,
   avec un recul si ça dépasserait la fin de la fenêtre du pivot.
3. **`_analyser_compatibilite(type_travaux_reference, type_travaux_a_modifier)`**
   (depuis le 2026-08-17) : croise les types de travaux (`TYPES_LOURDS` :
   REMPLACEMENT, CONSTRUCTION, REHABILITATION, RENFORCEMENT, MONTAGE,
   DEPLACEMENT / `TYPES_LEGERS` : INSPECTION, CONTROLES GENERAUX,
   NORMALISATION...) pour produire un niveau (`OPTIMAL`/`OK`/`ATTENTION`/
   `INCONNU`) et une note lisible, stockés dans
   `note_compatibilite_types`. Purement informatif : n'influence ni le choix
   du pivot ni le statut de la proposition.
4. **`_charge_disponible(...)`** : le chargé de consignation du travail
   a-t-il déjà un autre travail qui chevauche le nouveau créneau ?
   - Si occupé → `statut = BLOQUEE` (mais les dates calculées sont quand
     même enregistrées, pour montrer ce qui serait proposé si la charge
     était libre).
   - Si libre → `statut = EN_ATTENTE`.
   - **Depuis le 2026-08-23 (§9.8)** : la vérification porte aussi sur les
     fenêtres déjà proposées **dans la même analyse**, pas seulement sur les
     `Travail` déjà enregistrés en base. Sans ça, deux travaux d'un même
     groupe partageant le même chargé de consignation et alignés tous les
     deux sur la fenêtre du pivot ressortaient chacun `EN_ATTENTE`
     indépendamment — les appliquer tous les deux double-réservait
     silencieusement la même personne. Voir `alignements_proposes` dans
     `analyser_mois`.
   - `_charge_disponible` est aussi appelée en dehors de l'algorithme
     d'alignement : `TravailSerializer.validate()` (2026-08-23, §9.3) s'en
     sert pour valider tout `PATCH /travaux/{id}/` qui touche à la fois
     `heure_debut_planifie` et `duree` — c'est le cas de l'écran
     Réajustement manuel, qui ne passe pas par `analyser_mois`.

### 3.7 Déduplication

Avant de créer une proposition, le code cherche si une `PropositionAlignement`
**active** (`EN_ATTENTE` ou `BLOQUEE`) existe déjà pour le couple exact
`(travail_a_modifier, travail_reference)`. Si oui, elle est **réutilisée
telle quelle** (pas recalculée) — une `EN_ATTENTE` déjà calculée n'est pas
régénérée à chaque clic sur "Analyser". Les propositions terminales
(`ACCEPTEE`/`REFUSEE`) ne sont jamais réutilisées : elles restent dans
l'historique, et un nouveau conflit sur le même couple régénère une
proposition fraîche.

### 3.8 Nettoyage des propositions obsolètes — `_invalider_propositions_obsoletes`

À chaque analyse, avant de générer quoi que ce soit, le code compare les
couples `(travail_a_modifier, travail_reference)` qui correspondent à un
conflit **actuellement détecté** avec toutes les propositions `EN_ATTENTE`/
`BLOQUEE` déjà en base pour les travaux de la période analysée. Toute
proposition dont le couple n'est plus détecté (le conflit a été résolu
autrement — réajustement manuel, changement de segment/priorité/référence,
suppression...) est basculée en `REFUSEE`, avec `raison` préfixée de
`[Invalidée automatiquement — conflit résolu autrement]`. Cette étape a lieu
même si l'analyse ne détecte plus aucun chevauchement ce mois-ci.

### Exemple chiffré (scénario de référence)

Transport 08h00→18h00 (pivot, ne bouge pas) / Distribution 14h00→20h00
(durée 6h), même poste :

- `_peut_bouger(distribution)` → `True`.
- `_calculer_nouvel_horaire` : durée conservée = 6h ; `nouveau_debut` = 08h00
  (début du pivot) ; `nouvelle_fin` = 14h00 (≤ fin du pivot, pas d'ajustement).
- Charge de consignation libre sur 08h00→14h00 → `statut = EN_ATTENTE`.
- Résultat : `ancien_debut=14h00, ancienne_fin=20h00, nouveau_debut=08h00,
  nouvelle_fin=14h00`.

## 4. Modèle de données

### `Travail` (champs pertinents pour l'alignement)

| Champ | Rôle dans l'algorithme |
|-------|-------------------------|
| `segment` | TRANSPORT ne bouge jamais et coupe toujours au poste |
| `priorite` (P1/P2/P3) | P1 ne bouge jamais ; sert aussi au tri du pivot |
| `reference` → région, poste, rame, départ | Détermine si deux travaux partagent une ressource |
| `niveau_coupure` (POSTE(S)/RAME/DEPART(S)) | Granularité de la coupure, voir §3.2 |
| `charge_consignation` | Vérifié pour la disponibilité au nouveau créneau |
| `heure_debut_planifie` / `heure_fin_planifie` | Chevauchement + calcul du nouvel horaire |
| `travail_en_alignement` | Passé à `True` quand une proposition lui est appliquée |
| `alignement_verrouille` (2026-08-23) | Fixé manuellement par un gestionnaire (écran Réajustement, case "🔒 Fixer") : ne bouge plus jamais et devient prioritaire comme pivot (§3.5, §3.6). Purement manuel, ne se remet jamais à `False` tout seul. |

### `PropositionAlignement`

| Champ | Description |
|-------|--------------|
| `travail_a_modifier` / `travail_reference` | Le travail concerné et son pivot |
| `type_proposition` | `ALIGNEMENT_TRANSPORT` ou `ALIGNEMENT_TRAVAUX` selon le segment du pivot |
| `ancien_debut/fin`, `nouveau_debut/fin` | Horaires avant/après |
| `raison` | Texte explicatif généré automatiquement |
| `note_compatibilite_types` | Niveau + note de compatibilité des types de travaux, calculés par `_analyser_compatibilite` (§3.6). Purement informatif. |
| `conflit_charge_consignation` / `detail_conflit` | Renseignés si la charge de consignation est indisponible |
| `statut` | `EN_ATTENTE` / `ACCEPTEE` / `REFUSEE` / `BLOQUEE` |

## 5. Endpoints API

Base : `/planning/`

| Méthode | URL | Rôle |
|---------|-----|------|
| `POST` | `/plannings/analyser-mois/` | Lance l'analyse (mois courant par défaut, ou `{annee, mois}` en body). Seul point d'entrée de détection. |
| `GET` | `/plannings/{id}/propositions/?statut=...` | Liste les propositions d'un planning (filtre `statut` optionnel) |
| `POST` | `/plannings/{id}/appliquer-proposition/` | Body `{proposition_id}` — accepte et replanifie le travail |
| `POST` | `/plannings/{id}/refuser-proposition/` | Body `{proposition_id}` — refuse sans toucher au travail |
| `POST` | `/plannings/{id}/modifier-proposition/` | Body `{proposition_id, nouveau_debut, nouvelle_fin}` — ajuste la date proposée avant application (2026-08-17, §9.6) |

> ✅ Depuis le 2026-08-17, le `{id}` de planning dans l'URL de ces trois
> routes est vérifié : `self.get_object()` charge le planning (404 s'il
> n'existe pas) et la proposition est recherchée avec
> `.get(id=proposition_id, planning=planning)` — une proposition qui existe
> mais appartient à un autre planning renvoie 404 "Proposition introuvable"
> (même message que si elle n'existait pas, pour ne pas fuiter l'info). Voir §9.2.

Depuis le 2026-08-17, `modifier-proposition` (§9.6) permet d'ajuster
`nouveau_debut`/`nouvelle_fin` d'une proposition `EN_ATTENTE` ou `BLOQUEE`
avant de l'appliquer — ce n'est pas un `PATCH` générique mais une action
dédiée qui revalide la charge de consignation.

## 6. Cycle de vie d'une proposition

```
                 analyser-mois
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
  peut_bouger=False           peut_bouger=True
        │                           │
        ▼                    charge dispo ? ──non──► BLOQUEE ──refuser──► REFUSEE
     BLOQUEE                    │        ▲                  ▲
        │                      oui       └── modifier ──────┘ (si dispo à nouveau : EN_ATTENTE)
     refuser                    │
        │                       ▼
        ▼                  EN_ATTENTE ──modifier──► (recalcule dispo, reste EN_ATTENTE ou passe BLOQUEE)
     REFUSEE                │        │
                       appliquer   refuser
                             │        │
                             ▼        ▼
                         ACCEPTEE  REFUSEE
```

- `modifier-proposition` est refusée si le travail concerné ne peut pas
  bouger (`TRANSPORT`/`P1`, §3.6) : impossible de rendre applicable une
  proposition `BLOQUEE` pour cette raison en lui donnant simplement une
  autre date.

- `BLOQUEE` ne peut **pas** être appliquée (rejet 400), seulement refusée.
- Une proposition `ACCEPTEE` ou `REFUSEE` est **terminale** : la ré-appliquer
  ou la re-refuser renvoie une erreur 400 ("déjà '...'").
- Si le conflit sous-jacent existe toujours à la prochaine analyse après un
  refus, une **nouvelle** proposition `EN_ATTENTE` est créée à côté de
  l'ancienne `REFUSEE` (l'historique du refus est conservé) — depuis le
  2026-08-17, `analyser_mois` ne réutilise que les propositions **actives**
  (`EN_ATTENTE`/`BLOQUEE`) pour la déduplication ; une proposition terminale
  ne bloque plus jamais la régénération d'une proposition fraîche pour le
  même couple.
- **Auto-invalidation** (2026-08-17) : à chaque `analyser-mois`, toute
  proposition `EN_ATTENTE`/`BLOQUEE` dont le conflit n'est plus détecté
  (résolu par un réajustement manuel, un changement de segment/priorité/
  référence...) est automatiquement basculée en `REFUSEE`, avec un préfixe
  `[Invalidée automatiquement — conflit résolu autrement]` dans `raison`
  pour la distinguer d'un refus humain. Voir `_invalider_propositions_obsoletes`
  dans `alignement_service.py`.

## 7. Application et refus — effets exacts

### Appliquer (`appliquer-proposition`)

1. Rejette si `statut == BLOQUEE` (400).
2. Rejette si `statut != EN_ATTENTE` (400, déjà traitée).
3. **Revalidation (2026-08-23, §9.8)** : rappelle `_charge_disponible` à
   l'instant T (uniquement contre les `Travail` en base, pas besoin du
   traçage `alignements_proposes` ici car on applique une seule proposition
   à la fois). Si le chargé n'est plus disponible — par exemple parce
   qu'une autre proposition du même groupe partageant le même chargé vient
   d'être appliquée entre-temps — la proposition bascule en `BLOQUEE` et la
   requête est rejetée en **409** au lieu d'appliquer un changement qui
   double-réserverait la personne.
4. Sur `travail_a_modifier` : `heure_debut_planifie`, `heure_fin_planifie` ←
   les valeurs de la proposition ; `travail_en_alignement = True` ;
   `modifie_par` = utilisateur courant ; `.save()`.
5. Sur la proposition : `statut = ACCEPTEE`.

### Refuser (`refuser-proposition`)

1. Autorisé depuis `EN_ATTENTE` **ou** `BLOQUEE`.
2. Seul le `statut` de la proposition passe à `REFUSEE`. **Aucune écriture**
   sur le `Travail`.

### Modifier (`modifier-proposition`, 2026-08-17)

1. Autorisé depuis `EN_ATTENTE` **ou** `BLOQUEE`.
2. Rejette (400) si le travail concerné ne peut pas bouger (`_peut_bouger`
   == `False`, TRANSPORT/P1) — empêche de rendre applicable, via une
   simple modification de date, une proposition bloquée pour une raison
   qui n'a rien à voir avec la date.
3. Valide `nouveau_debut < nouvelle_fin`.
4. Recalcule `_charge_disponible(...)` sur le nouveau créneau et met à jour
   `nouveau_debut`, `nouvelle_fin`, `conflit_charge_consignation`,
   `detail_conflit` **et** `statut` (`EN_ATTENTE` si libre, `BLOQUEE` sinon)
   en conséquence — une modification peut donc débloquer une proposition,
   ou en bloquer une qui ne l'était pas.
5. Préfixe `raison` avec `[Modifiée manuellement par {utilisateur}]`.
6. **Aucune écriture** sur le `Travail` : comme pour Appliquer/Refuser, la
   modification ne prend effet sur le travail que si la proposition est
   ensuite appliquée.

### Ce qui n'est toujours pas fait

- **Refuser** ne revalide rien (inutile : aucune écriture n'a lieu).
- Ni Appliquer ni Refuser ne recalculent ou n'invalident les **autres**
  propositions du même groupe de conflit — seule la prochaine
  `analyser-mois` s'en chargera (`_invalider_propositions_obsoletes`, §3.8).

## 8. Consommation frontend

| Page / composant | Fichier | Ce qu'il utilise |
|-------------------|---------|-------------------|
| Page Alertes | [`AlertesView.jsx`](../../Plan_maintenance_Frontend/src/pages/G-Plan/Alertes/AlertesView.jsx) | `analyserMois(annee, mois)` + `buildGroupesDepuisChevauchements` — sélection libre du mois |
| Widget Dashboard | [`Dashboard/Alert/Alert.jsx`](../../Plan_maintenance_Frontend/src/pages/G-Plan/Dashboard/Alert/Alert.jsx) | `fetchAlertes()` (alias de `fetchGroupesConflits()`) — mois courant |
| Vue Calendrier | [`CalendarView.jsx`](../../Plan_maintenance_Frontend/src/pages/G-Plan/Calendar/CalendarView.jsx) | `fetchConflitIds()` (coloration des events) + `fetchGroupesConflits()` (cartes de conflit) — mois courant |
| Gantt avancé | [`AdvancedGantt.jsx`](../../Plan_maintenance_Frontend/src/pages/G-Plan/Gantt-Diag/details/AdvancedGantt.jsx) | `fetchPropositions`, `appliquerProposition`, `refuserProposition`, `modifierProposition` (2026-08-17) |
| Réajustement manuel | [`ReajustementAvance.jsx`](../../Plan_maintenance_Frontend/src/pages/G-Plan/Gantt-Diag/details/ReajustementAvance.jsx) | `patchTravail` — **ne passe pas par le système de propositions** (voir §9.3), mais le backend valide désormais la disponibilité du chargé de consignation (2026-08-23, `TravailSerializer.validate`). Champs désactivés pour tout travail `peut_bouger === false`. Case **🔒 Fixer** : envoie `alignement_verrouille: true` dans le PATCH pour figer l'alignement (uniquement pour les travaux encore déplaçables ; pas d'UI de déverrouillage pour l'instant). Erreur de charge affichée telle quelle si le backend rejette (400). |

Dans `AdvancedGantt.jsx`, le bouton "Modifier" de `PropCard` n'est proposé
que si la modification a un sens : proposition `EN_ATTENTE`, ou `BLOQUEE`
**pour cause de charge de consignation** (`conflit_charge_consignation`).
Une proposition `BLOQUEE` parce que le travail est non déplaçable n'offre
que "Réajuster manuellement" (le backend refuserait de toute façon la
modification, §7).

Toute la logique de génération de groupes de conflit est centralisée dans
[`gplanService.js`](../../Plan_maintenance_Frontend/src/services/gplanService.js) :
`buildGroupesDepuisChevauchements(chevauchements)` est la **seule**
implémentation de regroupement côté client — elle consomme directement le
résultat de `analyser-mois` (donc la vraie logique métier §3.2). Aucune page
ne doit réimplémenter un regroupement local (c'était le cas jusqu'au
2026-08-17, corrigé — voir Journal).

## 9. Points critiques connus

Liste de travail pour la suite. Statut mis à jour au fur et à mesure des
corrections.

| # | Statut | Problème | Détail |
|---|--------|----------|--------|
| 9.1 | ✅ Résolu (2026-08-17) | Regroupement de conflits divergent front/back | `gplanService.buildGroupes` reconstruisait les groupes par égalité de `reference.id`, ratant les conflits inter-segments (ex. Transport ↔ Distribution) qui n'ont jamais la même `Reference`. Dashboard et Calendrier ne montraient donc pas les mêmes conflits que la page Alertes. Remplacé par `buildGroupesDepuisChevauchements`, unique implémentation basée sur les `chevauchements` renvoyés par le backend. |
| 9.2 | ✅ Résolu (2026-08-17) | `appliquer-proposition` / `refuser-proposition` ignoraient le `{planning_id}` de l'URL | `appliquer_proposition`/`refuser_proposition` appellent désormais `self.get_object()` et recherchent la proposition avec `.get(id=proposition_id, planning=planning)`. Une proposition d'un autre planning renvoie 404 "Proposition introuvable", comme si elle n'existait pas. |
| 9.3 | ✅ Résolu (2026-08-23) | Le "Réajustement manuel" contourne entièrement le système de propositions | **Fait (2026-08-17)** : `ReajustementAvance.jsx` désactive l'édition (début + durée) pour tout travail `peut_bouger === false`, côté frontend uniquement. Les propositions devenues obsolètes après un réajustement manuel sont nettoyées automatiquement à la prochaine analyse (9.4). **Fait (2026-08-23, alignements fixés)** : nouveau champ `Travail.alignement_verrouille` (migration `0008`) — un travail verrouillé ne bouge plus jamais (`_peut_bouger`) et devient prioritaire comme pivot pour aligner les autres (`_score_priorite`, juste après TRANSPORT — voir §3.5). Case **🔒 Fixer** dans `ReajustementAvance.jsx`. **Fait (2026-08-23, charge de consignation)** : `TravailSerializer.validate()` appelle désormais `_charge_disponible` dès que `heure_debut_planifie` et `duree` sont envoyés ensemble (le cas du réajustement manuel) et rejette en 400 si le chargé est déjà occupé sur le nouveau créneau — protège tout `PATCH /travaux/{id}/`, pas seulement cet écran. **Reste à faire** : pas d'UI de déverrouillage d'un alignement fixé (nécessite un accès direct à l'API pour l'instant). |
| 9.4 | ✅ Résolu (2026-08-17) | Propositions jamais nettoyées | `analyser_mois` réutilisait les propositions existantes mais n'en supprimait aucune, quelle que soit la façon dont le conflit avait été résolu. Ajout de `_invalider_propositions_obsoletes` (§3.8) : à chaque analyse, toute proposition `EN_ATTENTE`/`BLOQUEE` dont le couple `(travail_a_modifier, travail_reference)` ne correspond plus à un conflit détecté est basculée en `REFUSEE` (motif préfixé `[Invalidée automatiquement...]`). Par ailleurs, la réutilisation par déduplication ne considère plus que les propositions actives (`EN_ATTENTE`/`BLOQUEE`) — une proposition terminale ne bloque plus la régénération d'une proposition fraîche pour le même couple (§3.7). |
| 9.5 | ✅ Résolu (2026-08-17) | `note_compatibilite_types` n'était plus jamais alimenté | Décision produit : rebrancher plutôt que retirer. `_analyser_compatibilite`, `TYPES_LOURDS`, `TYPES_LEGERS` réintégrés dans `alignement_service.py` et appelés dans `analyser_mois` (branche travail déplaçable) — voir §3.6. Le champ et l'UI `PropCard` redeviennent utiles sans changement de schéma. |
| 9.6 | ✅ Résolu (2026-08-17) | Pas de modification d'une proposition avant application | Ajout de `POST /plannings/{id}/modifier-proposition/` (§7) + bouton "Modifier" dans `PropCard` (`AdvancedGantt.jsx`) avec inputs `datetime-local` inline. Revalide la charge de consignation à chaque modification et refuse de modifier une proposition dont le travail n'est pas déplaçable (TRANSPORT/P1), pour ne pas rouvrir la faille que 9.3 a fermée. |
| 9.7 | ✅ Résolu (2026-08-17) | Doc de rôle désynchronisée | [`docs/roles/02_gestionnaire_de_planification.md`](../../Plan_maintenance_Frontend/docs/roles/02_gestionnaire_de_planification.md) référençait des endpoints qui n'existent plus (`/plannings/:id/analyser/`, `/plannings/:id/propositions/:pid/appliquer/`...). Corrigée pour correspondre à §5 de ce document, avec un lien vers celui-ci. |
| 9.8 | ✅ Résolu (2026-08-23) | Vérification de charge de consignation incomplète entre travaux d'un même groupe | `_charge_disponible` ne consultait que les `Travail` déjà enregistrés en base. Deux travaux d'un même groupe partageant le même chargé de consignation, tous deux alignés sur la fenêtre du pivot dans la **même** analyse, pouvaient chacun ressortir `EN_ATTENTE` indépendamment (aucun des deux n'a encore été réellement déplacé) : les appliquer tous les deux double-réservait silencieusement la personne, sans qu'`appliquer-proposition` ne revérifie rien à l'application. Ajout du traçage `alignements_proposes` dans `analyser_mois` (§3.6 point 4) + revalidation systématique dans `appliquer-proposition` (rejet 409 si la charge n'est plus disponible, §7). |
| 9.9 | ✅ Résolu (2026-08-25) | Une proposition déjà appliquée se régénérait indéfiniment | Repéré en test manuel (cas de démo septembre 2026) : après avoir appliqué une proposition, actualiser la page Alertes faisait réapparaître "la même" carte de conflit, et cliquer de nouveau sur Appliquer renvoyait 400 (la proposition d'origine était déjà `ACCEPTEE`, terminale). Cause : un couple aligné reste, par construction, en "chevauchement" (§3.4) ; comme la déduplication ne réutilise que les propositions **actives** (9.4), une proposition terminale ne bloquait plus rien et `analyser_mois` recréait donc, à chaque appel, une proposition `EN_ATTENTE` no-op pour ce couple déjà résolu. `analyser_mois` filtre désormais, par groupe, les membres déplaçables dont l'horaire calculé est déjà strictement identique à l'horaire actuel — le groupe disparaît de `chevauchements`/`propositions` s'il n'y a plus rien à proposer (§3.4). |

---

## Journal des modifications

| Date | Modification | Détail |
|------|---------------|--------|
| 2026-08-17 | Suppression de code mort | `analyser_et_proposer` (fonction non appelée par aucune vue depuis le retrait de la route `analyser-chevauchements`), `_analyser_compatibilite`, `TYPES_LOURDS`/`TYPES_LEGERS`, `ALIGNEMENT_COMPATIBLE` retirés de `alignement_service.py`. |
| 2026-08-17 | Unification du regroupement de conflits (§9.1) | Ajout de `planning_id` dans la réponse `analyser-mois` (backend) ; remplacement de `buildGroupes` par `buildGroupesDepuisChevauchements` côté frontend, utilisé par `AlertesView`, `CalendarView` et `Dashboard/Alert`. |
| 2026-08-17 | Correction doc de rôle (§9.7) | `docs/roles/02_gestionnaire_de_planification.md` aligné sur les endpoints réels + lien vers ce document. |
| 2026-08-17 | Scoping de appliquer/refuser-proposition par planning (§9.2) | `PlanningViewSet.appliquer_proposition`/`refuser_proposition` utilisent `self.get_object()` + filtrent la proposition par `planning=planning`. |
| 2026-08-17 | Blocage frontend de l'édition des travaux non déplaçables (§9.3, partiel) | `ReajustementAvance.jsx` : les champs début/durée sont désactivés quand `peut_bouger === false` ; `handleValider` exclut ces travaux des PATCH envoyés. Décision produit : pas de blocage backend générique sur `PATCH /travaux/{id}/`. |
| 2026-08-17 | Nettoyage automatique des propositions obsolètes (§9.4, §3.8) | Ajout de `_invalider_propositions_obsoletes` dans `alignement_service.py`, appelée à chaque `analyser_mois` avant les retours anticipés : toute proposition `EN_ATTENTE`/`BLOQUEE` dont le couple n'est plus détecté passe en `REFUSEE`. La déduplication (`propositions_existantes`) ne réutilise plus que les propositions actives (`EN_ATTENTE`/`BLOQUEE`). Aucune migration nécessaire (réutilise le statut `REFUSEE` existant plutôt qu'un nouveau statut dédié). |
| 2026-08-17 | Réintégration de la note de compatibilité des types (§9.5, §3.6) | `_analyser_compatibilite`, `TYPES_LOURDS`, `TYPES_LEGERS` réintroduits dans `alignement_service.py` et appelés dans `analyser_mois` pour remplir `note_compatibilite_types` à la création d'une proposition (branche travail déplaçable). Aucune migration nécessaire (champ déjà existant). |
| 2026-08-17 | Ajout de la modification de proposition (§9.6, §7) | Nouvelle action `POST /plannings/{id}/modifier-proposition/` (revalide `_charge_disponible`, refuse si `_peut_bouger` est `False`) + bouton "Modifier" dans `PropCard` (`AdvancedGantt.jsx`) avec édition inline `datetime-local`. `modifierProposition` ajouté à `gplanService.js`. |
| 2026-08-17 | Création de ce document | Première version. |
| 2026-08-23 | Alignements verrouillés manuellement (§9.3, §3.5, §3.6) | Nouveau champ `Travail.alignement_verrouille` (migration `0008_travail_alignement_verrouille`, à appliquer manuellement — pas d'environnement Django accessible pour `makemigrations`/`migrate` depuis cette session). `_peut_bouger` et `_score_priorite` en tiennent compte (priorité juste après TRANSPORT). `TravailSerializer` l'expose en lecture/écriture. `chevauchements_detectes` (analyser-mois) et `buildGroupesDepuisChevauchements` le propagent au frontend. Case "🔒 Fixer" ajoutée dans `ReajustementAvance.jsx`. `_raison_non_deplacable` distingue désormais TRANSPORT / verrouillé / P1 dans le motif de blocage. |
| 2026-08-23 | Charge de consignation vérifiée entre travaux d'un même groupe (§9.8, §3.6, §7) | `_charge_disponible` accepte un paramètre `alignements_proposes` ; `analyser_mois` y trace chaque fenêtre proposée `EN_ATTENTE` (fraîche ou réutilisée) sur toute l'analyse, tous groupes confondus, pour détecter un même chargé réservé deux fois dans le même lot. `appliquer-proposition` revalide `_charge_disponible` juste avant d'écrire sur le `Travail` et répond 409 (en re-basculant la proposition en `BLOQUEE`) si la charge n'est plus libre. |
| 2026-08-23 | Charge de consignation vérifiée dans le Réajustement manuel (§9.3, §3.6) | `TravailSerializer.validate()` appelle `_charge_disponible` (import cross-module depuis `alignement_service.py`) dès que `heure_debut_planifie` et `duree` sont fournis ensemble dans un `PATCH /travaux/{id}/`, et rejette en 400 (`{"charge_consignation": "..."}`) si le chargé est déjà occupé. `ReajustementAvance.jsx` affiche le message d'erreur renvoyé tel quel. 9.3 est maintenant entièrement résolu. |
| 2026-08-25 | Correction : proposition déjà appliquée régénérée indéfiniment (§9.9, §3.4) | `analyser_mois` filtre désormais, par groupe, les membres déplaçables déjà exactement calés sur la fenêtre du pivot (comparaison avec `_calculer_nouvel_horaire`) — plus de proposition `EN_ATTENTE` no-op régénérée à chaque analyse pour un couple déjà résolu, plus de groupe fantôme sur la page Alertes. `resume.total_chevauchements` (et le compte dans `message`) reflète désormais `len(chevauchements)` (groupes réellement actionnables), plus `len(groupes)` (union-find brut). Corrigé le scénario de démo Novembre 2026 (`seed_demo_harmonisation.py`) au passage : le pivot doit être TRANSPORT (P1 outrank toujours P2 dans `_score_priorite`, donc un pivot "P2 Maintenance poste" ne peut pas coexister avec un P1 dans le même groupe sans que ce soit le P1 qui devienne pivot). |
| 2026-08-25 | Correction : dates non parseables dans `analyser-mois` | `chevauchements[].reference.debut/fin` et `.travaux_en_conflit[].debut/fin` étaient formatés en texte `JJ/MM/AAAA HH:mm` (`strftime`) au lieu d'ISO 8601. `new Date(...)` sur ce format échoue (`Invalid Date`/`NaN`) dès que le jour dépasse 12, et donne une **date silencieusement fausse** sinon (JS interprète en MM/DD). Repéré via un avertissement React "two children with the same key, NaN" sur `ReajustementAvance.jsx` (clés de `weekDays` toutes égales à `"NaN"`). `alignement_service.py` renvoie désormais les `datetime` bruts (sérialisés en ISO par DRF), comme partout ailleurs dans l'API. Le formatage lisible pour l'affichage a été déplacé côté frontend : nouveau `formatDateTimeCourt` dans `gplanService.js`, utilisé par `buildGroupesDepuisChevauchements` (résumé `chevauchement`) et `AlertesView.jsx` ; `AdvancedGantt.jsx` réutilise son `fmt()` local. `ReajustementAvance.jsx` et `Calendar/components/calendar.jsx` (qui parsaient déjà ces dates pour du vrai calcul) sont corrigés sans changement de code, juste par la donnée désormais valide. |
