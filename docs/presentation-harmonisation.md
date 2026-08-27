# Harmonisation des plannings — support de présentation

> Module planification — ENEO / SONATREL. Audience : gestionnaires de
> planification. Durée indicative : 10–12 min. Environnement : jeu de
> données de démo sur 6 mois (voir [Repères techniques](#repères-techniques)).

Deux travaux de maintenance qui coupent la même ressource électrique au même
moment : le système les détecte, propose de les caler sur une seule et même
fenêtre d'indisponibilité, et laisse le gestionnaire décider. Ce document
déroule deux cas concrets, prêts à démontrer en direct.

Pour le détail complet de l'algorithme et des points techniques :
[`module-harmonisation-plannings.md`](module-harmonisation-plannings.md).

---

## Le principe, en 30 secondes

Avant d'entrer dans les cas de test, le vocabulaire partagé pour la suite de
la démo.

| # | Étape | Description |
|---|-------|-------------|
| 1 | **Analyser** | Le gestionnaire choisit un mois. Le système compare tous les travaux qui le touchent. |
| 2 | **Détecter** | Même poste, même rame ou même départ, et des horaires qui se chevauchent → conflit. |
| 3 | **Proposer** | Le travail le moins prioritaire est recalé sur la fenêtre du plus prioritaire (le pivot). |
| 4 | **Décider** | Le gestionnaire applique, refuse, ajuste la date — ou reprend la main manuellement. |

---

## Cas de test 1 — Valider une proposition

**Septembre 2026** — le cas d'usage central du module : deux entités
différentes, Transport et Distribution, interviennent sur le même poste
source sans le savoir. Le système propose de les regrouper sur une seule
coupure.

### Contexte

| | | Horaire |
|---|---|---|
| **Poste** | Transfo 90/15 kV — poste source de Nkongsamba | |
| **Transport** | Entretien du transformateur : coupure de tout le poste | 08/09 08:00 → 18:00 |
| **Distribution** | Remplacement d'isolateurs, départ NKG.D11 | 08/09 14:00 → 20:00 |

### Étapes

1. **Se connecter en gestionnaire de planification** — le rôle qui analyse
   les conflits et décide des propositions.
   `gestionnaire1 / Gestionnaire@1234`
2. **Ouvrir la page Alertes, sélectionner septembre 2026** — l'analyse se
   relance automatiquement à chaque changement de mois.
   `/dashboard/alertes`
3. **Cliquer sur la carte de conflit Nkongsamba** — elle ouvre le Gantt
   avancé avec le détail des deux travaux et la proposition générée.
4. **Lire la proposition** — le travail Distribution est proposé sur la
   fenêtre du Transport, durée conservée (6 h).
5. **Cliquer « Appliquer »** — le système revérifie la disponibilité du
   chargé de consignation avant d'écrire le changement.

### Avant / proposé

| | Avant | Proposé |
|---|---|---|
| **NKG.D11** | 14:00 → 20:00 | 08:00 → 14:00 |

La durée d'origine (6 h) est conservée ; seul le point de départ change,
aligné sur le début de la coupure Transport.

### Résultat

Le travail Distribution est replanifié à 08:00→14:00, marqué « en
alignement ». La proposition passe à `ACCEPTEE`. Une seule coupure de
terrain au lieu de deux.

### Ce que ça démontre

- **Détection inter-entités** : Transport et Distribution n'ont pas la même
  référence électrique — le rapprochement se fait par poste physique
  commun, pas par égalité de texte.
- **Le pivot ne bouge jamais** : un travail Transport coupe toujours tout le
  poste : c'est systématiquement lui la référence, jamais le contraire.
- **Revalidation à l'instant T** : la disponibilité du chargé de
  consignation est revérifiée juste avant l'écriture, pas seulement au
  moment du calcul.

---

## Cas de test 2 — Réajustement manuel

**Novembre 2026** — certains travaux ne doivent jamais être déplacés
automatiquement. Le système le sait, refuse de proposer un déplacement, et
renvoie la décision au gestionnaire.

### Contexte

| | | Horaire |
|---|---|---|
| **Poste** | Transfo N°1 — poste source de Garoua | |
| **Transport** (pivot) | Entretien transformateur 90/15 kV : coupure du poste source | 10/11 08:00 → 16:00 |
| **Distribution · P1 urgent** | Dépannage urgent, départ GRA.D31 | 10/11 10:00 → 14:00 |

### Étapes

1. **Alertes → novembre 2026** — le conflit Garoua apparaît comme les
   autres, mais sa proposition est bloquée.
2. **Ouvrir le conflit : la proposition est marquée `BLOQUEE`** — motif
   affiché : *« priorité P1 (urgent) »* — un travail P1 ne bouge jamais
   automatiquement, quel que soit le pivot.
3. **Cliquer « Réajuster manuellement »** — bascule vers l'écran de
   réajustement, calendrier de la semaine concernée.
   `/dashboard/reajustement-avance`
4. **Décaler l'horaire du travail concerné** — le champ du travail P1 est
   grisé et non modifiable : seul un travail réellement déplaçable peut
   être édité ici.
5. **Option — cocher « 🔒 Fixer »** — marque l'alignement comme définitif :
   le système ne le proposera plus jamais au déplacement, et s'appuiera
   dessus comme référence pour les futurs conflits.
6. **Valider** — le backend revérifie la disponibilité du chargé de
   consignation avant d'accepter le nouvel horaire.

### Avant / après

| | Proposition automatique | Décision humaine |
|---|---|---|
| **GRA.D31** | `BLOQUEE` | horaire choisi par le gestionnaire, hors système de propositions |

Le réajustement manuel n'est pas une proposition qu'on applique : c'est une
modification directe du travail, validée par les mêmes garde-fous (chargé
de consignation, travaux non déplaçables).

### Résultat

Le conflit est résolu par une décision humaine documentée. Si l'alignement
est fixé, il devient increvable : plus aucune analyse future ne le remettra
en cause, et les autres travaux du même poste s'aligneront dessus.

### Ce que ça démontre

- **Le système ne force jamais l'urgent** : TRANSPORT et P1 sont
  systématiquement exclus du déplacement automatique — la sécurité prime
  sur l'optimisation.
- **Mêmes garde-fous qu'en automatique** : le réajustement manuel vérifie
  désormais la charge de consignation — impossible d'y créer silencieusement
  un double-booking.
- **Verrouiller, c'est durable** : un alignement fixé ne se remet plus à
  disposition tout seul ; il faut une action humaine explicite pour le
  défaire.

---

## Pour aller plus loin, si le temps le permet

Quatre autres scénarios prêts à l'emploi :

| Mois | Scénario | Ce qu'il montre |
|------|----------|-------------------|
| **Octobre 2026** | Groupe à trois travaux | Trois travaux liés en chaîne (A–B–C) traités comme un seul groupe et calés sur le même pivot, avec deux niveaux de compatibilité de types affichés (OPTIMAL / ATTENTION). |
| **Décembre 2026** | Conflit de chargé de consignation | Le créneau proposé est déjà occupé par un travail sans rapport, ailleurs sur le réseau : la proposition ressort bloquée. |
| **Janvier 2027** | Chargé partagé dans le même groupe | Deux travaux du même conflit partagent le même chargé : un seul passe en attente, l'autre est bloqué — plus de double réservation silencieuse. |
| **Février 2027** | Alignement verrouillé sous un pivot Transport | Même verrouillé, un travail cède la place de pivot au Transport — mais reste bloqué pour un motif clairement distinct : « fixé manuellement ». |

---

## Repères techniques

### Comptes de démonstration

| Rôle | Identifiants |
|------|--------------|
| Gestionnaire | `gestionnaire1 / Gestionnaire@1234` |
| Opérateur Distribution | `operateur1 / Operateur@1234` |
| Opérateur Transport | `operateur2 / Operateur@1234` |
| Responsable | `responsable1 / Responsable@1234` |

### Jeu de données

À lancer une fois, dans cet ordre :

```
python manage.py seed_all
python manage.py seed_demo_harmonisation
```
