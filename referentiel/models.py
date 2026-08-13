from django.db import models
from django.utils.translation import gettext as _
import uuid


class Region(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.code

class Centrale(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    valeur = models.CharField(max_length=255)
    region = models.ForeignKey(
        Region, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='centrales'
    )
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.valeur


class TypeReferentiel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom


class Reference(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    valeur = models.CharField(max_length=500)
    entite_metier = models.ForeignKey(
        'user.EntiteMetier', on_delete=models.PROTECT,
        null=True, blank=True, related_name='references'
    )
    region = models.ForeignKey(
        Region, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='references'
    )
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.valeur


class ReferentielItem(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    valeur = models.CharField(max_length=255)
    reference = models.ForeignKey(
        Reference, on_delete=models.CASCADE, related_name='items'
    )
    type = models.ForeignKey(TypeReferentiel, on_delete=models.PROTECT, related_name='items')
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.type.nom}: {self.valeur}"


class Troncon(models.Model):
    """Liste indépendante des tronçons (Distribution), sans lien avec Reference/TypeReferentiel."""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    valeur = models.CharField(max_length=255, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.valeur

