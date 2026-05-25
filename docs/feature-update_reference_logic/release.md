# Release — `feature/update_reference_logic`

Changements introduits sur cette branche par rapport à `feature/workflow_validations`.

---

## Sommaire

1. [Modèles modifiés](#1-modèles-modifiés)
2. [Sécurité](#2-sécurité)
3. [Nouveaux endpoints](#3-nouveaux-endpoints)
4. [Seeders mis à jour](#4-seeders-mis-à-jour)
5. [Migrations — procédure d'application](#5-migrations--procédure-dapplication)

---

## 1. Modèles modifiés

### `referentiel.Reference` — nouveau champ `entite_metier`

Une référence appartient désormais à une **entité métier** (Production, Transport ou Distribution).

| Champ | Type | Avant | Après |
|-------|------|-------|-------|
| `entite_metier` | FK → `user.EntiteMetier` (nullable) | absent | ajouté |

**Migration SQL équivalente :**
```sql
ALTER TABLE referentiel_reference
  ADD COLUMN entite_metier_id CHAR(32) NULL,
  ADD CONSTRAINT fk_reference_entite
    FOREIGN KEY (entite_metier_id) REFERENCES user_entitemetier(id)
    ON DELETE RESTRICT;
```

---

### `referentiel.Centrale` — simplification

Les champs `nom`, `capacite_mw` et `actif` ont été supprimés. La table ne garde que `id` + `valeur`.

| Champ supprimé | Type |
|----------------|------|
| `nom` | CharField |
| `capacite_mw` | DecimalField |
| `actif` | BooleanField |

**Migration SQL équivalente :**
```sql
ALTER TABLE referentiel_centrale
  DROP COLUMN IF EXISTS nom,
  DROP COLUMN IF EXISTS capacite_mw,
  DROP COLUMN IF EXISTS actif;
```

> Si la table `referentiel_centrale` n'existait pas encore, aucune action n'est nécessaire — `migrate` la crée directement avec la bonne structure.

---

## 2. Sécurité

### Authentification requise sur tous les endpoints

Le paramètre `DEFAULT_PERMISSION_CLASSES` a été ajouté dans `core/settings.py` :

```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

**Impact :** tous les endpoints qui n'avaient pas de `permission_classes` explicite (notamment toute l'app `referentiel`) exigent désormais un **JWT valide** dans le header.

```http
Authorization: Bearer <access_token>
```

> Seul le endpoint de login reste public (`permission_classes = []` déjà défini dans `user/views.py`).

---

## 3. Nouveaux endpoints

### `GET /referentiel/references/?entite_metier_id=<uuid>`

Filtre les références par entité métier. Utile pour ne charger que les références pertinentes selon le segment de l'utilisateur.

```http
GET /referentiel/references/?entite_metier_id=<uuid_production>
Authorization: Bearer <token>
```

Réponse :
```json
[
  {
    "id": "...",
    "valeur": "PRODUCTION - EDEA_DCP_Groupe 01 - TR01",
    "entite_metier": { "id": "...", "name": "Production" },
    "items": [
      { "id": "...", "valeur": "DCP", "type": { "id": "...", "nom": "Ouvrage" } },
      { "id": "...", "valeur": "Groupe 01 - TR01", "type": { "id": "...", "nom": "Poste" } }
    ]
  }
]
```

---

## 4. Seeders mis à jour

### `seed_referentiel` — refonte complète

**Problèmes corrigés :**
- Les types d'items étaient mal nommés (`Tronçon` → inexistant dans l'Excel)
- Les colonnes Excel n'étaient pas correctement mappées
- Les références n'étaient pas liées à leur entité métier

**Structure réelle des feuilles Excel :**

| Colonne | En-tête Excel | Type créé | Feuilles concernées |
|---------|---------------|-----------|---------------------|
| 0 | `Segment` | `Segment` | toutes |
| 1 | `OUVRAGES (Centrales/lignes RT & postes RT)` | `Ouvrage` | toutes |
| 2 | `GR/TFO/POSTES/` | `Poste` | toutes |
| 3 | `DEPARTS` | `Départ` | distribution uniquement |

Chaque colonne produit un `ReferentielItem`. La valeur de la `Reference` est la concaténation de toutes les valeurs non vides séparées par `_`.

**Nombre d'items par référence :**

| Entité métier | Items par référence |
|---------------|---------------------|
| Production | 3 (Segment, Ouvrage, Poste) |
| Transport | 3 (Segment, Ouvrage, Poste) |
| Distribution | 4 (Segment, Ouvrage, Poste, Départ) |

**Types `TypeReferentiel` en base :**

| Avant | Après |
|-------|-------|
| Tronçon | *(supprimé)* |
| *(absent)* | Segment |
| Ouvrage | Ouvrage |
| Poste | Poste |
| Départ | Départ |

**Nouveau flag `--reset` :**
```bash
python manage.py seed_referentiel --reset
```
Supprime tous les `TypeReferentiel`, `Reference` et `ReferentielItem` existants avant de re-seeder. À utiliser pour corriger des données mal importées.

---

### `seed_centrales` — correctif

Le script utilisait l'ancien champ `nom` du modèle `Centrale`. Il utilise désormais `valeur`.

---

### Migrations non suivies par git

Les fichiers de migration (`*/migrations/0*.py`) sont maintenant dans `.gitignore`.

**Chaque développeur doit générer ses propres migrations localement** (voir section suivante).

---

## 5. Migrations — procédure d'application

### Cas 1 — Installation fraîche (nouvelle machine / nouvelle BD)

```bash
# 1. Démarrer les conteneurs
docker compose up -d

# Le serveur applique automatiquement les migrations au démarrage via :
# python manage.py migrate && gunicorn ...
```

Si les migrations ne sont pas encore présentes localement :
```bash
docker compose run --rm --entrypoint python web manage.py makemigrations
docker compose down && docker compose up -d
```

Puis lancer les seeders dans l'ordre :
```bash
docker compose exec web python manage.py seed_entite_metier
docker compose exec web python manage.py seed_referentiel
docker compose exec web python manage.py seed_unites_demanderesses
docker compose exec web python manage.py seed_types_travaux
docker compose exec web python manage.py seed_centrales
```

---

### Cas 2 — BD existante avec anciennes migrations

La BD contient déjà des données issues de `feature/workflow_validations`.
Les modèles `Centrale` et `Reference` ont changé de structure.

#### Étape 1 — Supprimer les anciennes migrations locales

```bash
# Linux / Mac / Git Bash
find . -path "*/migrations/[0-9]*.py" -delete

# PowerShell
Get-ChildItem -Recurse -Filter "0*.py" -Path "*/migrations" | Remove-Item
```

#### Étape 2 — Recréer les migrations

```bash
docker compose run --rm --entrypoint python web manage.py makemigrations
```

#### Étape 3 — Appliquer les migrations

**Option A — Reset complet (recommandé si les données peuvent être recréées par les seeders)**

```bash
docker compose down -v
docker compose up -d
```

**Option B — Migration incrémentale (si des données doivent être conservées)**

```bash
docker compose exec web python manage.py migrate
```

> En cas d'erreur `Duplicate column name`, utiliser l'Option A.

#### Étape 4 — Corriger les données du référentiel

Les types d'items et les liens vers `EntiteMetier` étaient incorrects. Re-seeder avec le flag `--reset` :

```bash
docker compose exec web python manage.py seed_entite_metier
docker compose exec web python manage.py seed_referentiel --reset
docker compose exec web python manage.py seed_unites_demanderesses
docker compose exec web python manage.py seed_types_travaux
docker compose exec web python manage.py seed_centrales
```

---

### Résumé des tables impactées

| Table | Changement |
|-------|-----------|
| `referentiel_reference` | Nouvelle colonne `entite_metier_id` |
| `referentiel_centrale` | Suppression de `nom`, `capacite_mw`, `actif` |
| `referentiel_typereferentiel` | Suppression de `Tronçon`, ajout de `Ouvrage` / `Poste` / `Départ` corrects |
| `referentiel_referentielitem` | Ré-import avec les bons types |
