from django.db import models
from django.utils.translation import gettext as _
import uuid


class Centrale(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    valeur = models.CharField(max_length=255)

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

    def __str__(self):
        return self.valeur


class ReferentielItem(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    valeur = models.CharField(max_length=255)
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE, related_name='items')
    type = models.ForeignKey(TypeReferentiel, on_delete=models.PROTECT, related_name='items')

    def __str__(self):
        return f"{self.type.nom}: {self.valeur}"
