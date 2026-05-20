from rest_framework import serializers 
from .models import Permission, Role, RolePermission, UserRole



class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= Permission  
        fields=["id", "nom", "code", "description","module"]
        
class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "nom", "code_role","description", "date_creation", "permissions"]

    def get_permissions(self, obj):
        # Utilisation du related_name 'role_permissions' défini dans le modèle
        role_permissions = obj.role_permissions.all().select_related('permission')
        permissions = [rp.permission for rp in role_permissions]
        return PermissionSerializer(permissions, many=True).data
        
class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= RolePermission 
        fields='__all__'
        
class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model= UserRole 
        fields='__all__'
        
#modifier le role assigné à un utilisateur
class UpdateUserRoleSerializer(serializers.ModelSerializer):
    role = serializers.SlugRelatedField( queryset=Role.objects.all(),slug_field='code_role')
    class Meta:
        model = UserRole
        fields = ['role']
       
        
class AssignRoleSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    role_code = serializers.CharField()


class AssignPermissionSerializer(serializers.Serializer):
    role_code = serializers.CharField()
    permission_code = serializers.CharField()


class CreateRoleSerializer(serializers.Serializer):
    nom_role = serializers.CharField(max_length=100)
    code_role = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)


class UpdateRoleSerializer(serializers.Serializer):
    code_role = serializers.CharField(max_length=50)
    nom = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)


class CreatePermissionSerializer(serializers.Serializer):
    nom_permission = serializers.CharField(max_length=100)
    code_permission = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    module = serializers.CharField(max_length=100)


class UpdatePermissionSerializer(serializers.Serializer):
    code_permission = serializers.CharField(max_length=50)
    nom = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    module = serializers.CharField(max_length=100)