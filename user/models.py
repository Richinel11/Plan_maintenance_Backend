from django.db import models
from django.utils.translation import gettext as _
import uuid
from django.contrib.auth.hashers import make_password

# Create your models here.
class EntiteMetier(models.Model):
    TYPE_CHOICES = [
        ('PROD', 'Production'),
        ('TRANS', 'Transport'),
        ('DIST', 'Distribution'),
    ]
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"


# Model For User

class Utilisateur(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    username = models.CharField(max_length=150, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    actif = models.BooleanField(default=False)
    ldap_req = models.BooleanField(default=False, blank=True, null=True)

    password = models.CharField(max_length=128, blank=True)
    first_connection = models.BooleanField(default=True)

    entite_metier = models.ForeignKey(EntiteMetier, on_delete=models.PROTECT, related_name="utilisateurs")

    role = models.ForeignKey("security.Role", on_delete=models.PROTECT, related_name="utilisateurs")

    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)

     # REQUIRED_FIELDS pour compatibilité Django
    REQUIRED_FIELDS = ['nom', 'prenom', 'email']

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username