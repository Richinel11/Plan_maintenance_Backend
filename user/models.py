from django.db import models
from django.utils.translation import gettext as _
import uuid
from django.contrib.auth.hashers import make_password
from security import models as securitymodels
from django.contrib.auth.models import AbstractBaseUser, AbstractUser
from .manager import UtilisateurManager




#Create your models here.

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class EntiteMetier(models.Model):
    TYPE_CHOICES = [
        ('PROD', 'Production'),
        ('TRANS', 'Transport'),
        ('DIST', 'Distribution'),
    ]
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.type}) "


# Model For User

class Utilisateur(AbstractUser):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    username = models.CharField(max_length=150, unique=True)
    entite_metier = models.ForeignKey(EntiteMetier, on_delete=models.SET_NULL, related_name="utilisateurs", blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_ldap = models.BooleanField(default=False, blank=True, null=True)
    # is_staff = models.BooleanField(default=False)
    password = models.CharField(max_length=255, blank=True)
    first_connection = models.BooleanField(default=False)
    last_connection_at = models.DateTimeField(default=None, blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.CharField(max_length=150, blank=True, null=True)
    modify_by = models.CharField( max_length=150, blank=True, null=True)
    modify_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    deleted_at = models.DateTimeField(default=None, blank=True, null=True)
    deleted_by = models.CharField( max_length=150, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)


    # Field add after de request of Blanche
    region = models.CharField(max_length=100, blank=True, null=True)
    

    USERNAME_FIELD = "username"
    
    objects = UtilisateurManager()


    def __str__(self):
        return self.username
    
    
