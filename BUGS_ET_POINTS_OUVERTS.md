# Bugs et Points Ouverts — Backend EneoPlan

Date de rédaction : 2026-06-20
Phase : Tests

---

## BUG-01 — Region absente sur le modèle `Planning`

### Description
Le modèle `Planning` n'a pas de champ `region` (FK vers `Region`). La région d'un
travail est accessible uniquement via la chaîne `Travail → reference → region`, ce qui
est une jointure indirecte à 2 niveaux.

### Impact
- Impossible de filtrer la liste des plannings directement par région via l'API
  (`GET /plannings/?region_id=...` ne fonctionne pas).
- Les tableaux de bord et rapports qui doivent afficher "les plannings de la région DRY"
  nécessitent des jointures complexes au lieu d'un simple filtre.
- Un utilisateur assigné à une région ne peut pas voir uniquement ses plannings.

### Correction suggérée
Ajouter `region = ForeignKey(Region, null=True, blank=True, on_delete=SET_NULL)`
sur `Planning`, créer la migration, puis ajouter `region_id` comme filtre dans
`PlanningViewSet.get_queryset()`.

---

## BUG-02 — Region absente sur le modèle `EntiteMetier`

### Description
`EntiteMetier` (Production, Transport, Distribution) n'a pas de lien direct vers `Region`.
La correspondance entité ↔ région doit être déduite indirectement via les références.

### Impact
- Impossible d'afficher ou filtrer les entités métier par région.
- Quand un utilisateur sélectionne une région dans l'interface, le dropdown des entités
  métier retourne toutes les entités plutôt que celles de la région concernée.
- Toute logique de droits d'accès basée sur `region × entite_metier` est impossible à
  implémenter proprement sans ce lien.

### Correction suggérée
Ajouter `region = ForeignKey(Region, null=True, blank=True, on_delete=SET_NULL)`
sur `EntiteMetier` et créer la migration correspondante.

---

## BUG-03 — `statut_travaux` sans logique d'évolution automatique

### Description
Le champ `statut_travaux` existe sur le modèle `Travail` (PLANIFIE, EN_COURS,
TERMINE, etc.) mais il n'y a aucune logique backend qui le fait évoluer
automatiquement. Le statut ne change que si l'utilisateur le modifie manuellement.

### Impact
- Un travail dont la `date_programmee` est passée reste à l'état PLANIFIE
  indéfiniment — les indicateurs de suivi sont donc faux.
- Les tableaux de bord (taux de réalisation, travaux en retard) ne reflètent
  pas la réalité du terrain.
- Les rapports DDR peuvent inclure des travaux qui auraient dû être clôturés.

### Correction suggérée
Deux approches possibles :
1. **Signal Django** : à chaque modification d'un `Travail`, vérifier les dates
   et mettre à jour le statut automatiquement.
2. **Tâche Celery périodique** : un job qui tourne chaque nuit et met à jour
   le statut de tous les travaux dont la date est dépassée.

À valider avec les clients : quelles sont les règles métier exactes de transition
de statut (ex : qui peut passer un travail à TERMINE, est-ce automatique ou manuel ?).

---

## BUG-04 — Endpoint `genererDDR` retourne 404

### Description
L'endpoint de génération de DDR (Demande de Rétablissement) retourne une erreur 404.
Le flux DDR est au cœur du processus métier d'ENEO — c'est le document qui formalise
une demande de coupure pour maintenance.

### Impact
- Les opérateurs ne peuvent pas générer de DDR depuis l'application.
- Tout le flux documentaire (création → validation → archivage) est bloqué.
- C'est l'une des fonctionnalités principales attendues par les clients.

### Pistes de diagnostic
- Vérifier que la vue `genererDDR` est bien enregistrée dans `urls.py`.
- Vérifier que l'URL appelée par le frontend correspond exactement à celle déclarée.
- Vérifier les permissions : l'utilisateur de test a-t-il le rôle requis ?
- Contrôler les logs Django au moment de l'appel pour voir si la 404 vient
  du routeur ou d'une vue interne.

---

## BUG-05 — Pages CCR non implémentées côté backend

### Description
Les pages CCR (Compte-Rendu de Chantier ou Centre de Conduite Réseau — à confirmer
avec les clients) ne sont pas encore fonctionnelles. Les vues, serializers ou endpoints
correspondants sont absents ou incomplets.

### Impact
- Les utilisateurs CCR ne peuvent pas accéder à leurs fonctionnalités depuis l'interface.
- Bloque la recette fonctionnelle de cette partie du projet.

### Correction suggérée
Définir précisément avec les clients :
1. Ce que couvre exactement le module CCR (quels écrans, quelles données).
2. Quels rôles ont accès à ces pages.
Ensuite implémenter les models/serializers/views/urls manquants.

---

## Récapitulatif

| Réf     | Problème                                  | Priorité | Effort estimé |
|---------|-------------------------------------------|----------|---------------|
| BUG-01  | Region absente sur `Planning`             | Haute    | Faible (migration + filtre) |
| BUG-02  | Region absente sur `EntiteMetier`         | Moyenne  | Faible (migration) |
| BUG-03  | `statut_travaux` sans évolution auto      | Haute    | Moyen (règles métier à définir) |
| BUG-04  | `genererDDR` retourne 404                 | Critique | Faible à Moyen (diagnostic d'abord) |
| BUG-05  | Pages CCR non implémentées                | Haute    | Élevé (spécification + dev) |
