from django.db import models
from django.utils.translation import gettext as _
import uuid
# Create your models here.

class Role(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=50, unique=True)
    code_role = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom
    
    
class Permission(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100) # element affiché pour l'utilisateur
    code = models.CharField(max_length=100, unique=True)  # element pour le backend
    module = models.CharField(max_length=100)  # planning, security, etc
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.code})"


class RolePermission(models.Model):
    role = models.ForeignKey(Role,on_delete=models.CASCADE,related_name="role_permissions")
    permission = models.ForeignKey(Permission,on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role} - {self.permission}"
    
    
    
class UserRole (models.Model):
    user = models.ForeignKey("user.Utilisateur", on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user} - {self.role}"


class WorkflowPermission(models.Model):
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    step = models.CharField(max_length=50) #savoir à quel niveau du workflow on se trouve