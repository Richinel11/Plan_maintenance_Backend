# README KPI — Rapport « Suivi des travaux prévisionnels »

> Document de passation à destination du développeur backend.
> Relevé effectué le **2026-09-01** sur le commit `07b70df`.
>
> Le frontend de ce rapport est terminé et branché. Il consomme un unique endpoint.
> Les points listés ci-dessous sont **côté backend uniquement** : rien n'a été modifié,
> tout est documenté pour que tu décides et appliques toi-même les correctifs.

---

## 1. Contexte

### La spécification de référence

Le rapport à reproduire est l'export du gestionnaire de planification :

```
Plan_maintenance_Frontend/EneoPlan_Front/src/assets/kpi.png
```

C'est **la seule spec qui fasse foi**. Elle contient 12 tuiles de synthèse et 5 tableaux.

### Le contrat d'API

Un seul appel alimente toute la page :

```
GET /travaux/rapport-suivi/?annee=2026&mois=6
```

- Vue : `planning/views.py:898` → `TravailViewSet.rapport_suivi`
- Calculs : `planning/rapport_suivi_service.py` (371 lignes)
- Permission : `IsAuthenticated`

### Ce qui fonctionne déjà

Pour être clair : **la base est bonne**. Ont été vérifiés et validés :

- La route répond `HTTP 200` avec des données réelles.
- La migration `0010` est appliquée (`heure_debut_reel`, `heure_fin_reel`,
  `duree_reelle_heures`, `end_realise_mwh`, segment `DACOR`, statut `ANNULE`).
- Le CORS autorise bien `localhost:5173`.
- La structure de la réponse correspond exactement aux 5 tableaux du rapport.
- Les conventions non documentées par le rapport source sont explicitées en tête
  du service — bonne pratique, ça a beaucoup aidé à la relecture.
- Le calcul par région (`Reference.region` / `Centrale.region` selon le segment)
  et le repli `end_realise_mwh` → `prevision_enf_mwh` sont corrects.

Les points ci-dessous sont des écarts par rapport au rapport de référence,
pas une remise en cause de l'architecture.

---

## 2. Défauts de calcul

### DÉFAUT 1 — « Travaux planifiés » utilise le mauvais périmètre de temps

**Gravité : élevée.** C'est le défaut principal, le n°2 en découle directement.

**Emplacement :** `planning/rapport_suivi_service.py:95-109`

**Le problème**

La fonction reçoit trois périmètres de temps, et en ignore un :

```python
def _evolution_par_segment(qs_ytd_m, qs_m, qs_ytd_m1):
#                          ↑            ↑      ↑
#                          cumul        mois M cumul
#                          jan → M      seul   jan → M-1

    for segment in SEGMENTS_PRINCIPAUX:
        qs_seg_m  = qs_m.filter(segment=segment)        # ligne 106 — mois M seul
        qs_seg_m1 = qs_ytd_m1.filter(segment=segment)   # ligne 107 — cumul
        planifies = qs_seg_m.count()                    # ligne 109
```

`qs_ytd_m` **n'est jamais référencé dans le corps de la fonction** (vérifiable :
il n'apparaît qu'une seule fois dans tout le fichier, dans la signature).

L'appelant lui passe pourtant bien le cumul (`rapport_suivi_service.py:310`) :

```python
evolution_lignes, evolution_total = _evolution_par_segment(qs_ytd, qs_m, qs_ytd_m1)
```

**Conséquence**

Dans le tableau « Evolution des TP mois en cours Vs M-1 », la colonne
« Travaux planifiés » compte **le mois M seul**, alors que la colonne voisine
« TP M-1 / YTD M-1 » compte **le cumul janvier → M-1**. Le tableau compare donc
un mois à cinq mois.

**Preuve par le rapport de référence**

| Élément du PNG | Valeur | Vérification |
|---|---|---|
| Colonne « Travaux planifiés », total | **2 432** | `184 + 1860 + 388` |
| Tuile « Travaux Planifiés (TP) » | **2 451** | `2 432 + 19 travaux sans segment` |
| Cumul janvier→juin du tableau segment/mois | **2 451** | `202+257+501+533+514+444` |
| Mois de juin **seul** | **444** | — |

La colonne vaut 2 432, soit le cumul — pas 444. Le périmètre attendu est donc
bien `qs_ytd_m`, celui qui est ignoré. Le paramètre inutilisé est la trace de
l'intention d'origine.

**Effet en cascade**

`taux_execution_travaux_pct` et `taux_conformite_planning_reference_pct` sont des
ratios dont le dénominateur est ce `planifies`. Les deux taux sont donc faux, et
les tuiles `taux_execution_tp_pct` / `taux_conformite_mois_m_pct` recopient ces
valeurs erronées (lignes 133 et suivantes).

**Correctif proposé** (une ligne)

```python
qs_seg_m = qs_ytd_m.filter(segment=segment)   # au lieu de qs_m
```

À vérifier au passage : `conformes` (ligne 112) doit suivre le même périmètre.

---

### DÉFAUT 2 — Deux tuiles END renvoient forcément la même valeur

**Gravité : élevée** (visible immédiatement à l'écran).

**Emplacement :** `planning/rapport_suivi_service.py:336-337`

**Le problème**

```python
"end_evitee_tpd_alignes_ytd_mwh":     evolution_total["gain_end_alignes_tpd_mwh"],
"realisation_end_alignee_mois_m_mwh": _gain_end_alignee(qs_m),
```

La première valeur provient du tableau Évolution qui — à cause du défaut 1 — a
calculé son gain END sur `qs_m`. La seconde appelle la même fonction
`_gain_end_alignee` sur le même `qs_m`.

**Même fonction + même queryset = même nombre, systématiquement.**

Le nom des champs annonce pourtant deux périmètres différents : `_ytd_` d'un
côté, `_mois_m_` de l'autre. Dans le rapport de référence ce sont bien deux
valeurs distinctes : **2 235,50** (cumul) et **2 068,00** (mois M).

**Correctif proposé**

Aucun correctif propre nécessaire : **corriger le défaut 1 suffit**. La première
tuile basculera alors sur le cumul, la seconde restera sur le mois M, et elles se
sépareront d'elles-mêmes.

---

### DÉFAUT 3 — Trois définitions différentes de la « durée moyenne réalisée »

**Gravité : moyenne.**

**Emplacement :** `planning/rapport_suivi_service.py:318-321` et `331`

**Le problème**

```python
duree_moy_realisee_mois_m = (
    _somme(qs_m.filter(statut_travaux='TERMINE'), F('duree_reelle_heures'))
    / executes_mois_m
) if executes_mois_m else 0.0
```

Le rapport de référence utilise **deux** définitions selon l'endroit :

| Où | Valeur | Formule |
|---|---|---|
| Tuile d'entête | **5,57** | `13 649,12 / 2 451` → ÷ **tous** les TP planifiés du cumul |
| Total du tableau « Durée des interruptions » | **14,10** | `13 649,12 / 968` → ÷ **seulement** les travaux réalisés |

Le service en produit une **troisième** : restreinte au mois M *et* aux `TERMINE`.
Elle ne correspond à aucune des deux.

**Nuance importante — le tableau, lui, est correct.**
`_duree_interruptions_par_segment` divise bien par le nombre de travaux ayant une
durée réelle, ce qui donne la définition à 14,10. **Seule la tuile dévie.**

**Correctif proposé**

Faire pointer la tuile sur l'indisponibilité réalisée totale divisée par le
nombre de TP planifiés du cumul :

```python
"duree_moyenne_realisee_mois_m_h":
    _round2(interruptions_total["indisponibilite_realisee_h"] / qs_ytd.count())
    if qs_ytd.count() else 0.0
```

À confirmer avec le métier (voir §4).

---

### DÉFAUT 4 — Les travaux BROUILLON sont comptés comme « planifiés »

**Gravité : élevée** — c'est ce qui fausse le plus les chiffres en production.

**Emplacement :** `planning/rapport_suivi_service.py:306` (et tous les
sous-calculs qui en dérivent)

**Le problème**

```python
qs_ytd = qs.filter(date_programmee__gte=debut_annee, date_programmee__lte=fin_mois_m)
```

Aucun filtre sur `statut_travaux`. Tous les travaux ayant une `date_programmee`
sont comptés comme « planifiés », **brouillons compris**.

**Mesure réelle en base (2026-09-01)**

```
TOTAL travaux : 309

BROUILLON    254      ← 82 % de la base
TERMINE       26
VALIDE        22
REPORTE        7

BROUILLON avec une date_programmee : 251  → comptés par le rapport
BROUILLON sans date_programmee     :   3
```

Ces brouillons ne viennent pas du seed de démo mais des **imports Excel** :

```
33  PLAN-202607-0008  Plannings distribution 2026.xlsx
33  PLAN-202607-0004  Plannings_10/2026 distribution.xlsx
30  PLAN-202606-0006  planning_production (1).xlsx
30  PLAN-202606-0013  planning_production de juillet.xlsx
28  PLAN-202606-0004  planning_transport_1_.xlsx
```

À l'import, les travaux sont créés avec le statut par défaut du modèle
(`Travail.statut_travaux` = `'BROUILLON'`).

**Conséquence**

251 brouillons gonflent tous les dénominateurs. Les taux d'exécution et de
conformité sont mécaniquement écrasés vers zéro, et la tuile « Travaux
Planifiés » affiche un volume qui ne correspond à aucune réalité opérationnelle.

**Correctif proposé** — décision métier requise (voir §4), puis par exemple :

```python
STATUTS_PLANIFIES = ['VALIDE', 'EN_COURS', 'TERMINE', 'REPORTE', 'ANNULE']
qs = qs.filter(statut_travaux__in=STATUTS_PLANIFIES)
```

---

## 3. Jeu de données de démonstration

**Ce n'est pas un bug**, mais ça bloque toute démo crédible.

`planning/management/commands/seed_kpi_avril_2026.py` a été écrit **avant** la
migration `0010`. Il ne remplit donc aucun des champs de réalisation.

**Mesure réelle en base**

```
heure_debut_reel        renseigné sur    0 / 309
heure_fin_reel          renseigné sur    0 / 309
duree_reelle_heures     renseigné sur    0 / 309
end_realise_mwh         renseigné sur    0 / 309
prevision_enf_mwh       renseigné sur    0 / 309
travail_en_alignement = True :           0
```

**Ce qui s'affiche vide à l'écran en conséquence**

| Élément du rapport | Cause |
|---|---|
| Colonnes « Indisponibilité Réalisée » et « Durée Moyenne Réalisée » | `duree_reelle_heures` vide |
| Tuile « Durée Moy Réalisée » | idem |
| Tableau « Travaux exécutés en alignement » — **entièrement vide** | aucun `travail_en_alignement=True` |
| Tuile « TP exécuté Align » | idem |
| Les 2 tuiles END + colonne « Gain en END TPD alignés » | aucun travail aligné, **et** `prevision_enf_mwh` vide donc le repli ne donne rien non plus |
| Tuile « TP Annulé » | aucun statut `ANNULE` en base |
| Ligne `DACOR` du tableau segment/mois | aucun travail sur ce segment |

Soit environ **40 % du rapport à zéro**.

**Suggestion :** compléter le seed pour que les travaux `TERMINE` portent
`heure_debut_reel` / `heure_fin_reel` (`duree_reelle_heures` se calcule alors
toute seule dans `Travail.save()`, `models.py:223-225`), un `end_realise_mwh`,
un `prevision_enf_mwh`, quelques `travail_en_alignement=True`, quelques `ANNULE`
et quelques travaux `DACOR`.

---

## 4. Décisions métier à trancher (pas des bugs)

Ces points demandent un arbitrage avec le gestionnaire de planification avant
d'écrire du code.

### 4.1 — Le « taux de conformité planning référence »

Aujourd'hui, c'est un **proxy** : « exécuté sans jamais avoir été reporté »
(`date_report_travaux` vide). C'est documenté honnêtement dans le docstring du
service.

Mais « conformité au planning de référence » signifie normalement : comparé à
une **version figée du planning au moment de sa validation**. Rien ne fige cette
baseline aujourd'hui — `Planning` n'a ni notion de version, ni snapshot.

C'est le seul point qui demande probablement un **nouveau modèle**.

### 4.2 — Que compte-t-on comme « planifié » ? (lié au défaut 4)

Faut-il exclure `BROUILLON` ? Et `SOUMIS` ? La réponse conditionne tous les
dénominateurs du rapport.

### 4.3 — Heures décimales ou H:MM ?

Le rapport libelle ses tuiles « Heure, Minutes » mais la valeur y est
**décimale** : `13 649,12 / 2 451 = 5,569` tombe exactement sur le 5,57 affiché.
Le service expose prudemment les deux formats (`*_h` et `*_hhmm`), et le
frontend consomme actuellement `*_h`. À confirmer.

### 4.4 — L'écart tuile / tableau du rapport de référence

Dans le PNG, la tuile et le tableau n'ont pas le même dénominateur :

| Indicateur | Tuile | Tableau | Écart |
|---|---|---|---|
| Taux exécution | 41,29 % (÷ 2 451) | 41,61 % (÷ 2 432) | les 19 travaux **sans segment** |
| Taux conformité | 34,97 % (÷ 2 451) | 35,24 % (÷ 2 432) | idem |

Le service pose actuellement `tuile = tableau`, il ne peut donc pas restituer les
deux. C'est mineur et cosmétique, mais visible si on compare au PNG.

### 4.5 — Segments et régions du rapport

- Le segment **DACOR** existe désormais dans le modèle mais aucun travail n'en porte.
- **POSTE SOURCE** apparaît comme une *région* dans le rapport (68 travaux) alors
  que c'est une entité. À clarifier.
- La ligne « région vide » du rapport (19 travaux) est bien gérée par le service
  (bucket `"Sans région"`), mais elle est triée alphabétiquement — elle atterrit
  entre `POSTE SOURCE` et `SLL` alors que le rapport la place en première ligne.

---

## 5. Récapitulatif

| # | Point | Type | Gravité | Correctif |
|---|---|---|---|---|
| 1 | `qs_ytd_m` ignoré → mauvais périmètre | Bug | Élevée | 1 ligne |
| 2 | 2 tuiles END identiques | Bug | Élevée | Réglé par le n°1 |
| 3 | 3ᵉ définition de la durée moyenne réalisée | Bug | Moyenne | Quelques lignes |
| 4 | BROUILLON comptés comme planifiés | Bug | Élevée | 1 filtre + décision 4.2 |
| 5 | Seed sans données de réalisation | Données | Moyenne | Compléter le seed |
| 6 | Taux de conformité = proxy | Métier | À arbitrer | Nouveau modèle probable |

**Ordre suggéré :** 1 → 4 → 3 → 5, puis les décisions métier.
Le n°2 se règle tout seul avec le n°1.

---

## Annexe — Formules décodées du rapport de référence

Toutes vérifiées arithmétiquement sur `kpi.png` (données au 14 juillet 2026).
Utile pour valider n'importe quel correctif.

| Constat | Conclusion |
|---|---|
| `202+257+501+533+514 = 2 007` = tuile « TP M-1 / YTD M-1 » | M-1 = mai → la tuile est un **cumul YTD**, pas un mois isolé |
| `2 007 + 444 (juin) = 2 451` = tuile « Travaux Planifiés » | **M = juin 2026**, TP = cumul janvier→juin |
| `1012 / 2451 = 41,29 %` (tuile) — `1012 / 2432 = 41,61 %` (tableau) | Taux d'exécution **cumul / cumul** ; écart = 19 travaux sans segment |
| `857 / 2451 = 34,97 %` — `857 / 2432 = 35,24 %` | 857 travaux conformes, même écart de 19 |
| `25 432,25 / 2451 = 10,38` ≈ tuile 10,39 | Durée moyenne prévue = ÷ tous les TP |
| `13 649,12 / 2451 = 5,569` = tuile 5,57 | Durée moyenne réalisée (tuile) = ÷ tous les TP |
| `13 649,12 / 968 = 14,10` = total du tableau | Durée moyenne réalisée (tableau) = ÷ les seuls réalisés |
| Ligne région vide = 19 ; `2 432 + 19 = 2 451` | Confirme le bucket « non renseigné » |
| Tableaux segment×mois et région×mois : total `2 596` chacun | Cohérents entre eux (janvier→juillet) |

---

## Annexe — Côté frontend (pour information)

Aucune action attendue de ta part, c'est juste pour situer.

```
src/services/RapportSuiviService.js              appel unique de l'endpoint
src/pages/G-Plan/KPI/RapportSuivi/
    RapportSuivi.jsx                             page + états de chargement
    components/Tuiles.jsx                        les 12 tuiles
    components/Tableaux.jsx                      les 5 tableaux
    components/styles.js                         mise en page
    components/format.js                         formatage FR
```

L'ancienne structure (`KpiResults.jsx`, `KPI1` → `KPI8`, `services/KpiData.js`)
est abandonnée mais pas supprimée — elle n'est simplement plus routée.
Les 7 endpoints qu'appelait `KpiData.js` (`/plannings-secteur/`, `/dispo-ipps/`,
`/maintenance-transport/`, `/distribution-poste/`, `/distribution-reseau/`,
`/impact-kpi/`, `/evaluation-ends/`) n'ont jamais existé côté backend : inutile
de les implémenter, ils ne correspondent à aucun bloc du rapport de référence.

**Note d'exploitation :** le backend tourne sous **gunicorn** dans Docker
(`django_api1`, port 8002), qui **ne recharge pas le code à chaud**. Après un
pull, il faut redémarrer le conteneur, sinon les workers continuent de servir
l'ancien code :

```bash
docker restart django_api1
```
