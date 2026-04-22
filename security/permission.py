from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from .services import user_has_permission, user_has_all_permissions

class HasPermission(BasePermission):
    """
    Pour APIView :
        permission_classes = [IsAuthenticated, HasPermission]
        required_permissions = ["MANAGE_ROLES"]
    """
    def has_permission(self, request: Request, view) -> bool:  # type: ignore[override]
        if not request.user or not request.user.is_authenticated:
            return False

        required_permission = getattr(view, 'required_permission', None)
        required_permissions = getattr(view, 'required_permissions', [])

        if required_permission:
            return user_has_permission(request.user, required_permission)

        if required_permissions:
            return user_has_all_permissions(request.user, required_permissions)

        return True


def HasPermissionFactory(*required_permissions):
    """
    Pour @api_view :
        @permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_ROLES')])
    """
    class _Permission(BasePermission):
        def has_permission(self, request: Request, view) -> bool:  # type: ignore[override]
            if not request.user or not request.user.is_authenticated:
                return False
            return user_has_all_permissions(request.user, list(required_permissions))

    return _Permission