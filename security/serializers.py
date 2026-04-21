from rest_framework import serializers

from .models import Permission, Role, RolePermission, UserRole, WorkflowPermission


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model= Role 
        fields= ["id", "nom", "code_role", "description", "date_creation"]
        

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model= Permission  
        fields=["id", "nom", "code", "description", "created_at"]
        
        
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