from django.db import models
from django.utils.translation import gettext as _
import uuid


# Create your models here.
from django.db import models

class Ouvrage(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    nom = models.CharField(max_length=150)
    type = models.CharField(max_length=100)

    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.nom


class Poste(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    nom = models.CharField(max_length=150)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    actif = models.BooleanField(default=False)
    def __str__(self):
        return self.nom


class Depart(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    nom = models.CharField(max_length=150)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    actif = models.BooleanField(default=False)
    def __str__(self):
        return self.nom


class Troncon(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    nom = models.CharField(max_length=150)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    actif = models.BooleanField(default=False)
    def __str__(self):
        return self.nom


class Localisation(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    def __str__(self):
        return f"{self.adresse} - {self.ville}"


class ReferenceReseau(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    code_reference = models.CharField(max_length=100, unique=True)
    libelle = models.CharField(max_length=255)
    ouvrage = models.ForeignKey(Ouvrage, on_delete=models.PROTECT)
    poste = models.ForeignKey(Poste, on_delete=models.PROTECT)
    depart = models.ForeignKey(Depart, on_delete=models.PROTECT)
    troncon = models.ForeignKey(Troncon, on_delete=models.PROTECT)
    localisation = models.ForeignKey(Localisation, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    actif = models.BooleanField(default=False)
    def __str__(self):
        return self.code_reference
