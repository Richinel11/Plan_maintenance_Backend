# Release — `feature/workflow_validations`

Documentation complète des changements introduits sur cette branche : nouveaux modèles, endpoints, seeders et guide d'utilisation.

---

## Sommaire

1. [Nouveaux modèles](#1-nouveaux-modèles)
2. [Modèles modifiés](#2-modèles-modifiés)
3. [Modèles supprimés](#3-modèles-supprimés)
4. [Endpoints — Referentiel](#4-endpoints--referentiel)
5. [Endpoints — User](#5-endpoints--user)
6. [Endpoints — Planning](#6-endpoints--planning)
7. [Endpoints — Pilotage (Workflow)](#7-endpoints--pilotage-workflow)
8. [Seeders](#8-seeders)

---

## 1. Nouveaux modèles

### `referentiel` app

#### `TypeReferentiel`
Représente un type d'élément de référence (ex : Tronçon, Ouvrage, Poste, Départ).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `nom` | CharField(100) | Nom unique du type |

#### `Reference`
Entrée de référence liée à un travail. Regroupe plusieurs items.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `valeur` | CharField(500) | Valeur composite (ex : `TRONCON_OUVRAGE_DEPART`) |

#### `ReferentielItem`
Composant élémentaire d'une référence (une colonne du classeur Excel).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `valeur` | CharField(255) | Valeur de l'item |
| `reference` | FK → Reference | Référence parente |
| `type` | FK → TypeReferentiel | Type de l'item |

---

### `user` app

#### `UniteDemanderesse`
Unité organisationnelle qui initie une demande de travaux.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `nom` | CharField(150) | Nom de l'unité |
| `entite_metier` | FK → EntiteMetier | Entité métier parente |
| `created_at` | DateTimeField | Date de création |

---

### `planning` app

#### `TypeActivite` (étendu)
Nouveau champ ajouté :

| Champ | Type | Description |
|-------|------|-------------|
| `entite_metier` | FK → EntiteMetier (nullable) | Entité métier associée |

---

### `pilotage` app

#### `Workflow`
Définit un processus de validation avec ses étapes et transitions.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `name` | CharField | Nom du workflow |
| `code` | CharField | Code unique |
| `description` | TextField | Description |

#### `WorkflowStep`
Étape d'un workflow.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `workflow` | FK → Workflow | Workflow parent |
| `name` | CharField | Nom de l'étape |
| `number` | PositiveIntegerField | Ordre de l'étape |
| `is_terminal` | BooleanField | Étape finale |

#### `WorkflowTransition`
Transition entre deux étapes d'un workflow.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `workflow` | FK → Workflow | Workflow parent |
| `from_step` | FK → WorkflowStep | Étape de départ |
| `to_step` | FK → WorkflowStep | Étape d'arrivée |
| `required_validations` | PositiveIntegerField | Nb de validations requises |

#### `WorkflowValidation`
Enregistrement d'une validation ou d'un rejet par un utilisateur.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `transition` | FK → WorkflowTransition | Transition concernée |
| `planning` | FK → Planning | Planning concerné |
| `validateur` | FK → Utilisateur | Utilisateur ayant validé/rejeté |
| `statut` | CharField | `APPROUVE` ou `REJETE` |
| `commentaire` | TextField | Commentaire optionnel |

#### `WorkflowHistory`
Journal des changements d'état du workflow pour un planning.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `planning` | FK → Planning | Planning concerné |
| `from_step` | FK → WorkflowStep | Étape précédente |
| `to_step` | FK → WorkflowStep | Nouvelle étape |
| `date` | DateTimeField | Date du changement |
| `par` | FK → Utilisateur | Auteur du changement |

---

## 2. Modèles modifiés

### `planning.Travail`
Champs ajoutés :

| Champ | Type | Description |
|-------|------|-------------|
| `reference` | FK → Reference (nullable) | Référence réseau du travail |
| `unite_demanderesse` | FK → UniteDemanderesse (nullable) | Unité demanderesse |

### `planning.Planning`
Champs ajoutés :

| Champ | Type | Description |
|-------|------|-------------|
| `workflow` | FK → Workflow (nullable) | Workflow de validation assigné |
| `current_step` | FK → WorkflowStep (nullable) | Étape courante du workflow |

---

## 3. Modèles supprimés

Les modèles suivants ont été retirés de l'app `referentiel` :

- `Ouvrage`
- `Poste`
- `Depart`
- `Troncon`
- `Localisation`
- `ReferenceReseau`

Remplacés par l'architecture flexible `TypeReferentiel → ReferentielItem → Reference`.

---

## 4. Endpoints — Referentiel

Base URL : `/referentiel/`

### Centrales

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/referentiel/centrales/` | Lister toutes les centrales |
| POST | `/referentiel/centrales/` | Créer une centrale |
| GET | `/referentiel/centrales/{id}/` | Détail d'une centrale |
| PUT/PATCH | `/referentiel/centrales/{id}/` | Modifier une centrale |
| DELETE | `/referentiel/centrales/{id}/` | Supprimer une centrale |

### Types de référentiel

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/referentiel/types/` | Lister les types |
| POST | `/referentiel/types/` | Créer un type |
| GET | `/referentiel/types/{id}/` | Détail d'un type |
| PUT/PATCH | `/referentiel/types/{id}/` | Modifier un type |
| DELETE | `/referentiel/types/{id}/` | Supprimer un type |

### Références

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/referentiel/references/` | Lister toutes les références |
| POST | `/referentiel/references/` | Créer une référence |
| GET | `/referentiel/references/{id}/` | Détail d'une référence |
| PUT/PATCH | `/referentiel/references/{id}/` | Modifier une référence |
| DELETE | `/referentiel/references/{id}/` | Supprimer une référence |
| GET | `/referentiel/references/{id}/items/` | Lister tous les items d'une référence |

**Exemple — récupérer les items d'une référence :**
```http
GET /referentiel/references/3fa85f64-5717-4562-b3fc-2c963f66afa6/items/
Authorization: Bearer <token>
```
Réponse :
```json
[
  { "id": "...", "valeur": "CENTRE", "type": { "id": "...", "nom": "Tronçon" } },
  { "id": "...", "valeur": "POSTE AKWA", "type": { "id": "...", "nom": "Poste" } },
  { "id": "...", "valeur": "DEPART SUD", "type": { "id": "...", "nom": "Départ" } }
]
```

### Items de référentiel

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/referentiel/items/` | Lister tous les items |
| POST | `/referentiel/items/` | Créer un item |
| GET | `/referentiel/items/{id}/` | Détail d'un item |
| PUT/PATCH | `/referentiel/items/{id}/` | Modifier un item |
| DELETE | `/referentiel/items/{id}/` | Supprimer un item |

**Filtres disponibles :**
- `?reference_id=<uuid>` — filtrer par référence
- `?type_id=<uuid>` — filtrer par type

---

## 5. Endpoints — User

Base URL : `/user/`

### Unités demanderesses

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/user/unites-demanderesses/` | Lister les unités |
| POST | `/user/unites-demanderesses/` | Créer une unité |
| GET | `/user/unites-demanderesses/{id}/` | Détail d'une unité |
| PUT/PATCH | `/user/unites-demanderesses/{id}/` | Modifier une unité |
| DELETE | `/user/unites-demanderesses/{id}/` | Supprimer une unité |

**Filtre disponible :**
- `?entite_metier_id=<uuid>` — filtrer par entité métier

**Exemple — créer une unité :**
```http
POST /user/unites-demanderesses/
Authorization: Bearer <token>
Content-Type: application/json

{
  "nom": "DR CENTRE",
  "entite_metier_id": "<uuid_entite_distribution>"
}
```

---

## 6. Endpoints — Planning

Base URL : `/planning/`

### Types d'activité

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/planning/types-activite/` | Lister les types d'activité |
| POST | `/planning/types-activite/` | Créer un type |
| GET | `/planning/types-activite/{id}/` | Détail d'un type |
| PUT/PATCH | `/planning/types-activite/{id}/` | Modifier un type |
| DELETE | `/planning/types-activite/{id}/` | Supprimer un type |

**Filtre disponible :**
- `?entite_metier_id=<uuid>` — filtrer par entité métier

---

### Plannings

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/planning/plannings/` | Lister les plannings |
| POST | `/planning/plannings/` | Créer un planning |
| GET | `/planning/plannings/{id}/` | Détail d'un planning |
| PUT/PATCH | `/planning/plannings/{id}/` | Modifier un planning |
| DELETE | `/planning/plannings/{id}/` | Supprimer un planning |
| POST | `/planning/plannings/{id}/assigner-workflow/` | Assigner un workflow et initialiser le step de départ |

**Exemple — créer un planning :**
```http
POST /planning/plannings/
Authorization: Bearer <token>
Content-Type: application/json

{
  "nom": "Planning Mai 2026",
  "entite_metier_id": "<uuid>"
}
```

**Exemple — assigner un workflow :**
```http
POST /planning/plannings/{id}/assigner-workflow/
Authorization: Bearer <token>
Content-Type: application/json

{
  "workflow_id": "<uuid_workflow>"
}
```
Le planning passe automatiquement sur le premier step du workflow (`number` le plus bas).

---

### Travaux

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/planning/travaux/` | Lister les travaux |
| POST | `/planning/travaux/` | Créer un travail |
| GET | `/planning/travaux/{id}/` | Détail d'un travail |
| PUT/PATCH | `/planning/travaux/{id}/` | Modifier un travail |
| DELETE | `/planning/travaux/{id}/` | Supprimer un travail |

#### Actions de workflow sur un travail

| Méthode | URL | Transition de statut | Condition |
|---------|-----|----------------------|-----------|
| POST | `/planning/travaux/{id}/soumettre/` | `BROUILLON → SOUMIS` | Statut doit être `BROUILLON` |
| POST | `/planning/travaux/{id}/valider/` | `SOUMIS → VALIDE` | Statut doit être `SOUMIS` |
| POST | `/planning/travaux/{id}/demarrer/` | `VALIDE → EN_COURS` | Statut doit être `VALIDE` |
| POST | `/planning/travaux/{id}/terminer/` | `EN_COURS → TERMINE` | Statut doit être `EN_COURS` |
| POST | `/planning/travaux/{id}/reporter/` | `* → REPORTE` | Requiert `date_report_travaux` |
| POST | `/planning/travaux/{id}/changer_statut/` | Libre | Corps : `{ "statut_travaux": "..." }` |

**Statuts disponibles :** `BROUILLON` · `SOUMIS` · `VALIDE` · `EN_COURS` · `TERMINE` · `REPORTE`

**Exemple — reporter un travail :**
```http
POST /planning/travaux/{id}/reporter/
Authorization: Bearer <token>
Content-Type: application/json

{
  "date_report_travaux": "2026-06-15"
}
```

#### Filtres et utilitaires

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/planning/travaux/par_segment/` | Filtrer par segment (`?segment=DISTRIBUTION\|TRANSPORT\|PRODUCTION`) |
| GET | `/planning/travaux/conflits/` | Lister les travaux dont les plages horaires se chevauchent sur la même référence |

**Exemple — travaux par segment :**
```http
GET /planning/travaux/par_segment/?segment=DISTRIBUTION
Authorization: Bearer <token>
```

**Exemple — créer un travail complet :**
```http
POST /planning/travaux/
Authorization: Bearer <token>
Content-Type: application/json

{
  "planning_id": "<uuid>",
  "segment": "DISTRIBUTION",
  "type_travaux_id": "<uuid>",
  "entite_metier_id": "<uuid>",
  "unite_demanderesse_id": "<uuid>",
  "reference_id": "<uuid>",
  "charge_consignation_id": "<uuid>",
  "consistance_travaux": "Remplacement du câble HTA",
  "troncons_consignes": "T1-T2",
  "localites_impactees": "Akwa, Bali",
  "heure_debut_planifie": "2026-06-01T08:00:00Z",
  "duree": 4,
  "unite_duree": "HEURES",
  "date_programmee": "2026-05-25"
}
```
Les champs `heure_fin_planifie` et `nombre_jours_avant_travaux` sont **calculés automatiquement** à la sauvegarde.

---

## 7. Endpoints — Pilotage (Workflow)

Base URL : `/pilotage/`

### Workflows

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/pilotage/workflows/` | Lister les workflows |
| POST | `/pilotage/workflows/` | Créer un workflow |
| GET | `/pilotage/workflows/{id}/` | Détail d'un workflow |
| PUT/PATCH | `/pilotage/workflows/{id}/` | Modifier un workflow |
| DELETE | `/pilotage/workflows/{id}/` | Supprimer un workflow |

### Steps

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/pilotage/steps/` | Lister les steps |
| POST | `/pilotage/steps/` | Créer un step |
| GET | `/pilotage/steps/{id}/` | Détail d'un step |
| PUT/PATCH | `/pilotage/steps/{id}/` | Modifier un step |
| DELETE | `/pilotage/steps/{id}/` | Supprimer un step |

### Transitions

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/pilotage/transitions/` | Lister les transitions |
| POST | `/pilotage/transitions/` | Créer une transition |
| GET | `/pilotage/transitions/{id}/` | Détail d'une transition |
| PUT/PATCH | `/pilotage/transitions/{id}/` | Modifier une transition |
| DELETE | `/pilotage/transitions/{id}/` | Supprimer une transition |

### Validations

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/pilotage/validations/` | Lister les validations |
| POST | `/pilotage/validations/` | Enregistrer une validation/rejet |
| GET | `/pilotage/validations/{id}/` | Détail d'une validation |

### Actions sur le workflow d'un planning

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/pilotage/plannings/{id}/transitions-disponibles/` | Transitions possibles depuis le step courant |
| POST | `/pilotage/plannings/{id}/executer-transition/` | Exécuter une transition (avancer d'étape) |
| POST | `/pilotage/plannings/{id}/rejeter/` | Rejeter la transition en cours |
| GET | `/pilotage/plannings/{id}/historique/` | Historique des changements d'étape |
| GET | `/pilotage/plannings/{id}/step-courant/` | Étape courante du planning |

**Exemple — exécuter une transition :**
```http
POST /pilotage/plannings/{id}/executer-transition/
Authorization: Bearer <token>
Content-Type: application/json

{
  "transition_id": "<uuid_transition>"
}
```

**Exemple — rejeter :**
```http
POST /pilotage/plannings/{id}/rejeter/
Authorization: Bearer <token>
Content-Type: application/json

{
  "transition_id": "<uuid_transition>",
  "commentaire": "Dossier incomplet, pièces manquantes."
}
```

---

## 8. Seeders

Le fichier Excel **`BD asset - système électrique (1) (1).xlsx`** doit être présent dans le dossier `docs/`.

### Seeders disponibles

| Ordre | Commande | Modèle alimenté | Source |
|-------|----------|----------------|--------|
| 1 | `seed_entite_metier` | `EntiteMetier` | Données fixes |
| 2 | `seed_referentiel` | `TypeReferentiel`, `Reference`, `ReferentielItem` | Feuilles Excel (3 premières) |
| 3 | `seed_unites_demanderesses` | `UniteDemanderesse` | Feuille « Unité demanderesse » |
| 4 | `seed_types_travaux` | `TypeActivite` | Feuille « Type de travaux » |
| 5 | `seed_centrales` | `Centrale` | Feuille « Centrale thermique sollicitée » |

> L'ordre est obligatoire : les seeders 2-4 dépendent de `seed_entite_metier`.

### Exécution

**En local :**
```bash
python manage.py seed_entite_metier
python manage.py seed_referentiel
python manage.py seed_unites_demanderesses
python manage.py seed_types_travaux
python manage.py seed_centrales
```

**Via Docker :**
```bash
docker compose exec web python manage.py seed_entite_metier
docker compose exec web python manage.py seed_referentiel
docker compose exec web python manage.py seed_unites_demanderesses
docker compose exec web python manage.py seed_types_travaux
docker compose exec web python manage.py seed_centrales
```

### EntiteMetier créées par `seed_entite_metier`

| Nom | Type |
|-----|------|
| Production | PROD |
| Transport | TRANS |
| Distribution | DIST |

### Comportement en cas de ré-exécution

Tous les seeders utilisent `get_or_create` : relancer un seeder ne crée pas de doublons.

```
[+] créée          → nouvel enregistrement inséré
[ ] déjà existante → ignoré, aucune modification
```

### Réinitialisation complète

```bash
python manage.py shell -c "
from referentiel.models import ReferentielItem, Reference, TypeReferentiel, Centrale
from user.models import UniteDemanderesse
from planning.models import TypeActivite
TypeActivite.objects.all().delete()
Centrale.objects.all().delete()
UniteDemanderesse.objects.all().delete()
ReferentielItem.objects.all().delete()
Reference.objects.all().delete()
TypeReferentiel.objects.all().delete()
print('Tables vidées.')
"

python manage.py seed_entite_metier
python manage.py seed_referentiel
python manage.py seed_unites_demanderesses
python manage.py seed_types_travaux
python manage.py seed_centrales
```
