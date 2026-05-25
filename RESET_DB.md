# Réinitialisation de la base de données

> A utiliser après un refactoring majeur des modèles (ex: split de `PlanningTravaux` en `Planning` + `Travail`).

## Contexte

Suite au refactoring du module `planning`, les tables suivantes ont été restructurées :

- `planning_planningtravaux` → supprimée
- `planning_planning` → nouvelle table (enveloppe du planning)
- `planning_travail` → nouvelle table (travail individuel, lié à un planning)

Les apps `exploitation` et `pilotage` ont aussi été mises à jour pour pointer vers les nouveaux modèles.

---

## Procédure complète

### 1. Supprimer les anciennes migrations

```bash
docker compose exec web bash -c "find planning/migrations exploitation/migrations pilotage/migrations -name '0*.py' -delete"
```

Vérifier que seuls les `__init__.py` restent :

```bash
docker compose exec web bash -c "ls planning/migrations/ exploitation/migrations/ pilotage/migrations/"
```

### 2. Recréer les migrations

```bash
docker compose exec web python manage.py makemigrations
```

### 3. Réinitialiser la base de données

**Option A — Supprimer les volumes Docker (recommandé en dev)**

```bash
docker compose down -v
docker compose up -d
```

**Option B — Vider uniquement les tables concernées (si données à conserver ailleurs)**

```bash
docker compose exec db mysql -u plan -p mydb -e "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE IF EXISTS exploitation_demanderetrait, exploitation_notearret, pilotage_workflowhistory, planning_planningtravaux, planning_planning, planning_travail; SET FOREIGN_KEY_CHECKS = 1;"
```

### 4. Appliquer les migrations

```bash
docker compose exec web python manage.py migrate
```

### 5. Recréer un superutilisateur (si besoin)

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Structure des modèles après refactoring

```
Planning
├── id, nom, code (auto)
├── entite_metier → EntiteMetier
├── workflow → Workflow
├── current_step → WorkflowStep
├── cree_par / modifie_par → Utilisateur
└── travaux[] → [Travail]

Travail (lié à un Planning)
├── id, segment, reference (auto)
├── planning → Planning  (obligatoire)
├── entite_metier → EntiteMetier
├── ouvrage / poste / depart / troncon
├── type_travaux, type_reseau
├── programmation temporelle
├── indicateurs PRODUCTION
├── statut_travaux
└── cree_par / modifie_par → Utilisateur

DemandeRetrait
└── travail → Travail  (était planning → PlanningTravaux)

NoteArret
└── travail → Travail  (était planning → PlanningTravaux)

WorkflowHistory
└── planning → Planning  (était planning → PlanningTravaux)
```

---

## Points d'attention

- Le workflow (`workflow`, `current_step`) est porté par **Planning**, pas par Travail.
- Les transitions DDR/NAPT dans `exploitation/views.py` accèdent au step via `travail.planning.current_step`.
- L'URL `ddr/generer/<uuid>` prend désormais un `travail_id` et non plus un `planning_id`.


okay, check la branche sur la quelle je suis et cree une release qui explique les modif fait et quoi appliquer sur la bd et comment les a[ppliquer