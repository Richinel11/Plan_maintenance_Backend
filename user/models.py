from django.db import models
from django.utils.translation import gettext as _
import uuid
from django.contrib.auth.hashers import make_password
from security import models as securitymodels

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

class Utilisateur(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_ldap = models.BooleanField(default=False, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True)
    first_connection = models.BooleanField(default=False)
    last_connection_at = models.DateTimeField(default=None, blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.CharField(max_length=150, blank=True, null=True)
    modify_by = models.CharField( max_length=150, blank=True, null=True)
    modify_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    deleted_at = models.DateTimeField(default=None, blank=True, null=True)
    deleted_by = models.CharField( max_length=150, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.username
    
    objects = SoftDeleteManager()

    all_objects = models.Manager()
