# Journal des Corrections Backend — ENEOPLAN

Ce fichier documente toutes les modifications apportées au backend Django,
avec pour chaque correction : la cause du bug, le fichier modifié, et la solution.

---

## BUG-001 — Backend ne démarre pas : connexion MySQL refusée

**Date :** 2026-05-29
**Priorité :** CRITIQUE
**Statut :** ✅ Corrigé

### Symptôme
- En local : `Access denied for user 'root'@'...' (using password: YES)`
- En Docker (`django_api1`) : `Can't connect to server on '127.0.0.1'` → crash loop

### Cause
`core/settings.py` contenait une configuration de base de données **hardcodée** (`USER=root`,
`PASSWORD=P@ssw0rd`, `HOST=127.0.0.1`) qui :
- Ne correspondait pas au mot de passe réel du MySQL Docker (`password`)
- Ne fonctionnait pas à l'intérieur du container Docker (MySQL y est accessible via le nom `db`, pas `127.0.0.1`)

### Fichiers modifiés
| Fichier | Modification |
|---|---|
| `core/settings.py` | Suppression de la config hardcodée. Remplacement par lecture depuis `os.environ.get(...)` |
| `.env` | `DJANGO_DATABASE_HOST` : `db` → `127.0.0.1` / `PORT` : `3306` → `3307` (pour usage local) |
| `docker-compose.yml` | Ajout de `environment: DJANGO_DATABASE_HOST=db / PORT=3306` pour overrider le `.env` à l'intérieur du container Docker |

### Règle de fonctionnement après correction
- **Local (`python manage.py runserver`)** : lit `.env` → HOST=127.0.0.1, PORT=3307
- **Docker (`docker-compose up`)** : lit `.env` PUIS override HOST=db, PORT=3306

---

## BUG-002 — Email utilisateur non sauvegardé à la création

**Date :** 2026-05-29
**Priorité :** HAUTE
**Statut :** ✅ Corrigé

### Symptôme
L'email saisi dans le formulaire de création d'utilisateur n'apparaît ni dans la liste
ni dans le formulaire de modification (champ vide en base de données).

### Cause
Dans `user/manager.py`, la méthode `_create_user` acceptait `email` comme paramètre
mais ne le transmettait **jamais** à `self.model(...)` lors de la création de l'instance.
L'email était reçu puis silencieusement ignoré.

```python
# AVANT (bugué)
def _create_user(self, username, email, is_staff, is_superuser, password, **extra_fields):
    user = self.model(username=username, is_staff=is_staff, ...)  # email absent !

# APRÈS (corrigé)
def _create_user(self, username, email, is_staff, is_superuser, password, **extra_fields):
    user = self.model(username=username, email=email, is_staff=is_staff, ...)
```

### Fichier modifié
| Fichier | Ligne | Modification |
|---|---|---|
| `user/manager.py` | 9 | Ajout de `email=email` dans l'appel à `self.model(...)` |

### Impact
Tous les utilisateurs créés avant ce correctif ont leur champ `email` à `NULL` en base.
Ils peuvent le renseigner via le formulaire de modification.

---

## BUG-003 — Rôle et état de retour (go_back_to) invisibles dans la liste des transitions

**Date :** 2026-05-29
**Priorité :** HAUTE
**Statut :** ✅ Corrigé

### Symptôme
Dans la page de détail d'un workflow, la colonne "Rôle Compétent" affiche `—`
et la colonne "Retour Arrière" n'affiche pas l'étape de destination,
même lorsqu'une transition est correctement créée.

### Cause — Deux problèmes distincts

**Problème A — `role` absent du sérialiseur de lecture**
`WorkflowTransitionSerializer` (utilisé pour les réponses GET) ne retournait pas le rôle.
Or, le rôle n'est pas stocké directement sur `WorkflowTransition` mais sur le modèle
`WorkflowValidation` lié (via `transition.validations`).

**Problème B — Mismatch de nom de champ**
Le frontend cherchait `t.go_back_step` pour afficher l'état de retour,
mais le sérialiseur backend nomme ce champ `go_back_to` (nom du FK dans le modèle).

### Fichiers modifiés
| Fichier | Modification |
|---|---|
| `pilotage/serializers.py` | Ajout du champ `role_info` (SerializerMethodField) dans `WorkflowTransitionSerializer`. Il récupère le rôle depuis `transition.validations.select_related('role').first()`. Ajout de commentaires explicatifs sur l'architecture. |

> Le correctif frontend (`t.go_back_step` → `t.go_back_to` et `t.role` → `t.role_info`)
> est documenté dans le journal frontend.

### Architecture à retenir
```
WorkflowTransition
  └── validations (related_name) → WorkflowValidation
        └── role → security.Role
```
Le rôle compétent pour une transition n'est jamais sur la transition elle-même,
il faut toujours passer par `WorkflowValidation`.

---

## BUG-004 — Route `/plannings/<id>/travaux/` inexistante

**Date :** 2026-05-29
**Priorité :** HAUTE
**Statut :** ✅ Corrigé

### Symptôme
Quand l'utilisateur clique sur un planning dans la liste, la page de détail
reste vide (aucun travail affiché). L'erreur console est :
`404 Not Found : /plannings/<uuid>/travaux/`

Même problème après la création d'un travail via "Nouveau Travail" :
la redirection vers le détail du planning échoue à charger les travaux.

### Cause
Le frontend appelait `GET /plannings/<id>/travaux/` pour récupérer les travaux
d'un planning donné. Cette route imbriquée **n'existait pas**.

`TravailViewSet` est un router indépendant (`/travaux/`).
Il n'y avait aucune action imbriquée dans `PlanningViewSet` pour accéder aux travaux.

### Solution choisie
Ajout d'une nouvelle action `@action` dans `PlanningViewSet` :
`GET /plannings/<id>/travaux/`

**Choix délibéré** : ne pas modifier les routes existantes (`/travaux/` reste intact),
mais créer une route supplémentaire ancrée sur le planning pour la navigation contextuelle.

### Fichier modifié
| Fichier | Modification |
|---|---|
| `planning/views.py` | Ajout de l'action `travaux_du_planning` dans `PlanningViewSet` |

### Route créée
```
GET /plannings/<uuid>/travaux/
```
Retourne la liste des travaux appartenant au planning identifié par `<uuid>`,
triés par date de création décroissante.

---

---

## BUG-005 — ValidationError : `"undefined" is not a valid UUID` sur `/references/`

**Date :** 2026-05-29
**Priorité :** HAUTE
**Statut :** ✅ Corrigé

### Symptôme
```
ValidationError at /references/
['"undefined" is not a valid UUID.']
Request URL: http://localhost:8002/references/?entite_metier_id=undefined
```
L'erreur survient lors de la visualisation des détails d'un planning.

### Cause
En JavaScript, quand une variable est `undefined` et insérée dans un template literal,
elle devient la chaîne `"undefined"` :
```javascript
// entiteMetierId = undefined
api.get(`references/?entite_metier_id=${entiteMetierId}`)
// → GET /references/?entite_metier_id=undefined  ← chaîne invalide
```

Côté backend, le `get_queryset` faisait `if entite_id:` — la chaîne `"undefined"`
est **truthy** donc passe la condition, puis Django tente de la convertir en UUID → crash.

Même bug latent dans `getUnites` (`/users/unites-demanderesses/?entite_metier_id=undefined`).

### Correction en deux couches (défense en profondeur)

**Couche 1 — Frontend (`referencetielService.js`)** :
```javascript
// AVANT
api.get(`references/?entite_metier_id=${entiteMetierId}`)

// APRÈS
const url = entiteMetierId ? `references/?entite_metier_id=${entiteMetierId}` : `references/`;
api.get(url)
```
Même correction appliquée à `getUnites`.

**Couche 2 — Backend (`referentiel/views.py`)** :
```python
# Garde défensive contre les valeurs invalides envoyées par JavaScript
VALEURS_INVALIDES = {'undefined', 'null', ''}
if entite_id and entite_id not in VALEURS_INVALIDES:
    qs = qs.filter(entite_metier_id=entite_id)
```

### Fichiers modifiés
| Fichier | Modification |
|---|---|
| `referencetielService.js` (frontend) | Condition ternaire pour `getReferences` et `getUnites` |
| `referentiel/views.py` | Garde défensive dans `ReferenceViewSet.get_queryset()` |

---

---

## BUG-006 — Suppression d'un planning : `500 ProgrammingError` — table `planning_propositionalignement` inexistante

**Date :** 2026-05-29
**Priorité :** CRITIQUE
**Statut :** ✅ Corrigé

### Symptôme
`DELETE /plannings/<id>/` retourne une erreur 500 :
```
ProgrammingError: (1146, "Table 'mydb.planning_propositionalignement' doesn't exist")
```
Le bouton "Supprimer" dans la liste des plannings n'a aucun effet visible côté utilisateur.

### Cause
Le modèle `PropositionAlignement` a été ajouté dans `planning/models.py` mais **aucune migration Django n'a jamais été générée** pour ce modèle.

Lors d'un `DELETE /plannings/<id>/`, Django cherche à CASCADE-supprimer les `PropositionAlignement` liées au planning (FK avec `on_delete=CASCADE`). La requête SQL échoue car la table `planning_propositionalignement` n'existe pas en base.

`python manage.py showmigrations planning` montrait `[X] 0001_initial` et `[X] 0002_initial` — ces migrations ne contenaient pas `PropositionAlignement`. Django considérait le modèle comme "non migratable" mais ne détectait pas l'écart.

### Correction
```bash
python manage.py makemigrations planning
# → Crée 0003_alter_travail_nombre_jours_avant_travaux_and_more.py
#   ~ Alter field nombre_jours_avant_travaux on travail
#   + Create model PropositionAlignement

python manage.py migrate planning
# → Applying planning.0003_... OK
```

### Fichier créé
| Fichier | Contenu |
|---|---|
| `planning/migrations/0003_alter_travail_nombre_jours_avant_travaux_and_more.py` | Création de la table `planning_propositionalignement` + altération du champ `nombre_jours_avant_travaux` |

### Règle à retenir
Après tout ajout de modèle dans `models.py`, toujours vérifier avec :
```bash
python manage.py makemigrations --check
```
Si la commande retourne exit code 1, des migrations sont manquantes.

---

## Conventions pour ce journal

- Chaque bug reçoit un identifiant `BUG-XXX` incrémental.
- Le statut peut être : `🔄 En cours` / `✅ Corrigé` / `⏳ Reporté`
- Toujours documenter : la cause exacte, les fichiers touchés, et l'architecture impliquée.
- Ne jamais supprimer une entrée corrigée — elle sert de référence historique.
