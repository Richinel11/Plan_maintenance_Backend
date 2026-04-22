from rest_framework import serializers 
from .models import Permission, Role, RolePermission, UserRole, WorkflowPermission



class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= Permission  
        fields=["nom", "code", "description"]
        
class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["nom", "code_role",  "date_creation", "permissions"]

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
        

        
class WorkflowPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= WorkflowPermission 
        fields='__all__'
        
class AssignRoleSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    role_code = serializers.CharField()


class AssignPermissionSerializer(serializers.Serializer):
    role_code = serializers.CharField()
    permission_code = serializers.CharField()