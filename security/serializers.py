from rest_framework import serializers

from .models import Permission, Role, RolePermission, UserRole, WorkflowPermission


class RoleSerializer(serializers.Serializer):
    class Meta:
        model= Role 
        fields= ["id", "nom", "code_role", "description", "date_creation"]
        

class PermissionSerializer(serializers.Serializer):
    class Meta:
        model= Permission  
        fields='__all__'
        
        
class RolePermissionSerializer(serializers.Serializer):
    class Meta:
        model= RolePermission 
        fields='__all__'
        
class UserRoleSerializer(serializers.Serializer):
    class Meta:
        model= UserRole 
        fields='__all__'
        
class WorkflowPermissionSerializer(serializers.Serializer):
    class Meta:
        model= WorkflowPermission 
        fields='__all__'