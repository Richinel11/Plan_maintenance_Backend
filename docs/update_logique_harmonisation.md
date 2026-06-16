# Mise à jour — Logique d'harmonisation des travaux

**Date :** 2026-06-04  
**Fichiers modifiés :**
- `planning/views.py` — action `conflits()`
- `planning/alignement_service.py` — fonctions `_partage_ressource`, `_ressources_communes`, `_detecter_groupes`, `analyser_et_proposer`

---

## Contexte

La procédure **EO PR EGS QAC 222 F-A** définit les règles d'harmonisation entre les trois segments (PRODUCTION, TRANSPORT, DISTRIBUTION). L'analyse du code existant a révélé quatre problèmes et une règle métier manquante. Ce document décrit chaque correction.

---

## 1. Règle intra-service manquante (`views.py` + `alignement_service.py`)

### Problème
La détection de conflits reposait uniquement sur la présence d'items OUVRAGE ou TRONÇON dans la référence des deux travaux. Or, la procédure stipule que pour deux travaux du **même segment**, la référence commune suffit comme signal d'alerte — même si aucun item de type OUVRAGE/TRONÇON n'est renseigné dans la référence.

Exemple non détecté avant la correction : deux travaux DISTRIBUTION partageant la même référence `REF-045` mais dont les items de référence sont vides.

### Correction
**`views.py` — `conflits()`** : ajout d'une vérification explicite :
```python
intra_meme_ref = (
    t1.segment == t2.segment
    and t1.reference_id is not None
    and t1.reference_id == t2.reference_id
)
```
Si `intra_meme_ref` est vrai ET qu'il y a chevauchement temporel → conflit.

**`alignement_service.py` — `_partage_ressource()`** : même logique ajoutée en tête de fonction, avant la vérification des items.

---

## 2. Nouvelle règle — opportunités d'harmonisation sur la même semaine (`views.py`)

### Problème
L'harmonisation ne se limite pas aux conflits de simultanéité. Deux travaux planifiés sur la **même semaine** (ex. lundi et mercredi) sur le même ouvrage ou tronçon peuvent être regroupés pour éviter deux coupures séparées. Cette logique était absente.

### Correction
Dans `conflits()`, après la vérification du chevauchement temporel, un second test est appliqué aux paires sans chevauchement :

```python
sem1 = t1.heure_debut_planifie.isocalendar()[:2]  # (année, semaine ISO)
sem2 = t2.heure_debut_planifie.isocalendar()[:2]
if sem1 == sem2:
    ids_opportunites.add(str(t1.id))
    ids_opportunites.add(str(t2.id))
```

La réponse de l'endpoint retourne désormais deux listes distinctes :
```json
{
  "conflits": ["id1", "id2"],
  "opportunites_harmonisation": ["id3", "id4"]
}
```

Un travail déjà en conflit avéré n'apparaît pas dans les opportunités (`ids_opportunites -= ids_en_conflit`).

---

## 3. N+1 requêtes dans `analyser_et_proposer` (`alignement_service.py`)

### Problème
La fonction `analyser_et_proposer` utilisait `select_related` mais les fonctions `_partage_ressource` et `_ressources_communes` appelaient `travail.reference.items.filter(...)`. Django ne peut pas utiliser le cache prefetch avec `.filter()`, ce qui déclenchait une requête SQL supplémentaire pour chaque paire de travaux comparée.

### Correction
Deux changements :

1. Ajout de `prefetch_related('reference__items__type')` dans toutes les requêtes de `analyser_et_proposer`.

2. Remplacement de `.filter(type__nom__in=...)` par `.all()` avec filtrage Python dans `_partage_ressource` et `_ressources_communes` :
```python
items_a = {
    (item.valeur, item.type.nom)
    for item in travail_a.reference.items.all()  # utilise le cache prefetch
    if item.type.nom in TYPES_CONFLIT
}
```

---

## 4. Regroupement en étoile → clôture transitive (`alignement_service.py`)

### Problème
L'ancienne `_detecter_groupes` vérifiait uniquement si `T_B` était en conflit avec `T_A` (l'ancre de départ). En cas de conflits transitifs (T1↔T2 et T2↔T3, mais pas T1↔T3 directement), T3 n'était pas ajouté au groupe de T1 et pouvait être ignoré si T2 était déjà marqué comme visité.

### Correction
Remplacement par un parcours en largeur (**BFS**) qui construit les composantes connexes du graphe de conflits :

```python
# Construction du graphe
adjacence: dict = {t.id: set() for t in travaux_valides}
for i, t_a in enumerate(travaux_valides):
    for t_b in travaux_valides[i + 1:]:
        if _partage_ressource(t_a, t_b) and _periodes_se_chevauchent(...):
            adjacence[t_a.id].add(t_b.id)
            adjacence[t_b.id].add(t_a.id)

# BFS pour trouver les composantes
while file:
    courant = file.pop(0)
    for voisin_id in adjacence[courant]:
        if voisin_id not in visites:
            ...
```

Tous les travaux liés transitivement sont maintenant regroupés correctement.

---

## 5. Analyse limitée à un seul planning → étendue à tous les plannings (`alignement_service.py`)

### Problème
`analyser_et_proposer` ne chargeait que les travaux du planning passé en paramètre. Les conflits inter-service (ex. un travail DISTRIBUTION en conflit avec un travail TRANSPORT d'un planning différent) n'étaient jamais détectés par ce service.

### Correction
La fonction charge maintenant deux ensembles de travaux :

1. **Travaux du planning cible** — pour lesquels des propositions seront créées.
2. **Travaux des autres plannings** — dans la même fenêtre temporelle, pour servir de référence dans la détection inter-service.

```python
# Fenêtre temporelle du planning cible
debut_min = min(t.heure_debut_planifie for t in travaux_planning)
fin_max   = max(t.heure_fin_planifie   for t in travaux_planning)

# Travaux externes dans cette fenêtre
travaux_externes = Travail.objects.exclude(planning=planning).filter(
    heure_debut_planifie__lt=fin_max,
    heure_fin_planifie__gt=debut_min,
    ...
)
```

L'analyse est exécutée sur `travaux_planning + travaux_externes`. Les propositions sont ensuite filtrées pour ne cibler que les travaux du planning cible :

```python
for travail in [t for t in autres if t.id in ids_planning]:
    ...
```

---

## Résumé des fichiers modifiés

| Fichier | Fonction | Nature de la modification |
|---|---|---|
| `planning/views.py` | `conflits()` | Règle intra-service + règle semaine + nouvelle réponse |
| `planning/views.py` | `groupes_conflits()` | Nouvel endpoint — groupes structurés pour les alertes |
| `planning/alignement_service.py` | `_partage_ressource()` | Règle intra-service + `.all()` pour prefetch |
| `planning/alignement_service.py` | `_ressources_communes()` | `.all()` pour prefetch |
| `planning/alignement_service.py` | `_detecter_groupes()` | BFS (clôture transitive) |
| `planning/alignement_service.py` | `analyser_et_proposer()` | Cross-planning + prefetch_related |

---

## 6. Nouvel endpoint — `GET /travaux/groupes-conflits/` (`views.py`)

### Pourquoi

Les alertes du frontend ont besoin de données **structurées par groupe**, pas seulement d'une liste d'IDs. L'endpoint `conflits` existant ne retourne que des IDs plats — impossible de savoir quels travaux sont en conflit ensemble, sur quel ouvrage, ni sur quelle plage horaire.

`analyserChevauchements` ne convient pas non plus : il crée des propositions en base à chaque appel, ce qui est trop lourd pour un simple affichage d'alertes.

### Ce que fait l'endpoint

Lecture seule. Retourne deux types de groupes :

**CONFLIT** — travaux avec chevauchement temporel sur la même ressource :
```json
{
  "id_groupe": "a3f1b2c4d5e6",
  "type": "CONFLIT",
  "statut": "OUVERT",
  "ressources_communes": ["OUVRAGE : Poste Delta"],
  "chevauchement": "Lun 02/06 08h00 → 12h00",
  "nb_travaux": 3,
  "travaux": [
    { "id": "...", "reference": "TR-2024-0892", "segment": "TRANSPORT", ... }
  ]
}
```

**OPPORTUNITE** — travaux sans chevauchement mais sur la même semaine et même ressource :
```json
{
  "id_groupe": "f7e8d9c0b1a2",
  "type": "OPPORTUNITE",
  "statut": "OUVERT",
  "ressources_communes": ["TRONCON : Ligne HTA-44"],
  "semaine": "S23-2026",
  "nb_travaux": 2,
  "travaux": [ ... ]
}
```

### Champ `statut`

- `OUVERT` — au moins un travail du groupe n'a pas encore `travail_en_alignement = True`
- `RESOLU` — tous les travaux du groupe ont `travail_en_alignement = True`

### Champ `id_groupe`

Hash MD5 (12 caractères) des IDs des travaux triés. Stable tant que la composition du groupe ne change pas. Utilisé par le frontend pour identifier une alerte de manière unique.

### Logique de détection

- **CONFLIT** : réutilise `_detecter_groupes()` de `alignement_service.py` (BFS, clôture transitive).
- **OPPORTUNITE** : construit un graphe distinct où deux travaux sont voisins s'ils partagent une ressource, sont dans la même semaine ISO, et ne se chevauchent pas. Les composantes connexes sont extraites par BFS. Les travaux déjà tous en conflit sont exclus des opportunités.
