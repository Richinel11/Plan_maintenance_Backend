from rest_framework.permissions import BasePermission
from .services import user_has_permission


class HasPermission(BasePermission):
    def has_permission(self, request, view):
        
        user = request.user
        #verifier si l'utilisateur est connecté
         
        if not user or not user.is_authenticated:
            return False
        
        required_permission = getattr(view, 'required_permission', None)
        required_permissions = getattr(view, 'required_permissions', None)

        # Une seule permission
        if required_permission:
            return user_has_permission(user, required_permission)

        # Plusieurs permissions (ALL)
        if required_permissions:
            return all(user_has_permission(user, p) for p in required_permissions)

        return True
        