# Documentation — Filtrage par Entité Métier (Backend)

Ce fichier décrit ce que le backend doit implémenter pour que chaque
liste déroulante du formulaire "Créer un travail" n'affiche que les
données correspondant à l'entité métier (Transport / Distribution /
Production) sélectionnée par l'opérateur.

---

## État actuel des endpoints (ce qui fonctionne déjà)

Les endpoints suivants acceptent déjà le paramètre `entite_metier_id`
et filtrent leurs résultats en conséquence. **Ne pas modifier.**

| Endpoint | Paramètre accepté | Champ filtré |
|---|---|---|
| `GET /references/` | `?entite_metier_id=<uuid>` | `Reference.entite_metier` |
| `GET /charges-consignation/` | `?entite_metier_id=<uuid>` | `ChargeConsignation.entite_metier` |
| `GET /users/unites-demanderesses/` | `?entite_metier_id=<uuid>` | `UniteDemanderesse.entite_metier` |

---

## Ce qui doit être ajouté / modifié

### 1. `GET /plannings/` — Filtre par entité métier

**Problème actuel :** l'endpoint retourne TOUS les plannings sans distinction
d'entité. Le frontend filtre côté client sur la page 1 uniquement,
ce qui est incomplet si les données sont paginées.

**Ce qu'il faut faire :**
Ajouter le support du paramètre `?entite_metier=<uuid>` sur la ViewSet
`PlanningViewSet` pour filtrer les plannings par entité métier.

**Implémentation suggérée (Django REST Framework) :**

```python
# Dans planning/views.py ou planning/filters.py

import django_filters
from .models import Planning

class PlanningFilter(django_filters.FilterSet):
    entite_metier = django_filters.UUIDFilter(field_name='entite_metier__id')

    class Meta:
        model = Planning
        fields = ['entite_metier']
```

```python
# Dans la ViewSet (planning/views.py)

from django_filters.rest_framework import DjangoFilterBackend
from .filters import PlanningFilter

class PlanningViewSet(viewsets.ModelViewSet):
    ...
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlanningFilter
```

**Appel frontend attendu après implémentation :**
```
GET /plannings/?entite_metier=<uuid>&page=1
```

**Réponse attendue (format déjà existant, pas de changement) :**
```json
{
  "count": 12,
  "next": "http://localhost:8000/plannings/?entite_metier=<uuid>&page=2",
  "previous": null,
  "results": [
    {
      "id": "<uuid>",
      "nom": "Planning Transport Mai 2026",
      "code": "PLN-001",
      "entite_metier": { "id": "<uuid>", "name": "Transport" },
      ...
    }
  ]
}
```

---

### 2. `GET /types-activite/` — Filtre par entité métier

**Problème actuel :** l'endpoint retourne TOUS les types d'activité
sans filtre. Le champ "Type de travaux" du formulaire affiche donc
des types qui n'appartiennent pas au service sélectionné.

**Ce qu'il faut faire :**
Deux cas possibles selon le modèle :

**Cas A — Le modèle `TypeActivite` possède déjà une FK vers `EntiteMetier` :**
Ajouter le paramètre `?entite_metier_id=<uuid>` dans la ViewSet.

```python
class TypeActiviteFilter(django_filters.FilterSet):
    entite_metier_id = django_filters.UUIDFilter(field_name='entite_metier__id')

    class Meta:
        model = TypeActivite
        fields = ['entite_metier_id']
```

**Cas B — Le modèle `TypeActivite` n'a pas de FK vers `EntiteMetier` :**
Ajouter une FK (nullable pour ne pas casser l'existant) :

```python
# Dans le modèle TypeActivite (referentiel/models.py ou planning/models.py)

from user.models import EntiteMetier

class TypeActivite(models.Model):
    nom = models.CharField(max_length=100)
    entite_metier = models.ForeignKey(
        EntiteMetier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='types_activite'
    )
```

Puis générer et appliquer la migration :
```bash
python manage.py makemigrations
python manage.py migrate
```

**Appel frontend attendu après implémentation :**
```
GET /types-activite/?entite_metier_id=<uuid>
```

**Réponse attendue :**
```json
[
  { "id": 1, "nom": "Maintenance" },
  { "id": 2, "nom": "Inspection" },
  { "id": 3, "nom": "Remplacement" }
]
```

---

### 3. `GET /centrales/` — Filtre (spécifique Production)

**Problème actuel :** l'endpoint retourne toutes les centrales sans filtre.
Ce champ n'est visible que pour le service Production, mais si plusieurs
entités métier de type Production existent, il faut filtrer.

**Ce qu'il faut faire :**
Ajouter le support de `?entite_metier_id=<uuid>` si le modèle
`CentraleThermique` possède une FK vers `EntiteMetier`. Sinon,
vérifier si toutes les centrales sont communes à toutes les entités
Production — dans ce cas aucun changement n'est nécessaire.

```python
class CentraleFilter(django_filters.FilterSet):
    entite_metier_id = django_filters.UUIDFilter(field_name='entite_metier__id')

    class Meta:
        model = CentraleThermique
        fields = ['entite_metier_id']
```

**Appel frontend attendu après implémentation :**
```
GET /centrales/?entite_metier_id=<uuid>
```

---

## Résumé des changements à faire côté backend

| Endpoint | Action requise | Priorité |
|---|---|---|
| `GET /plannings/` | Ajouter filtre `?entite_metier=<uuid>` via DjangoFilterBackend | **Haute** |
| `GET /types-activite/` | Ajouter FK `entite_metier` sur le modèle + filtre `?entite_metier_id=<uuid>` | **Haute** |
| `GET /centrales/` | Ajouter filtre `?entite_metier_id=<uuid>` si pertinent | Moyenne |

## Note importante sur le paramètre utilisé

Le frontend utilise deux noms de paramètres selon l'endpoint existant :
- `entite_metier_id` → pour références, charges, unités (déjà en place)
- `entite_metier` → pour les plannings (à implémenter, filtre sur l'ID de la FK)

Pour harmoniser à terme, privilégier `entite_metier_id` sur tous les
nouveaux endpoints.
