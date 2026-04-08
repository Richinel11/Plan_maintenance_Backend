from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet,
    PermissionViewSet,
    AssignRoleToUserView,
    RemoveRoleFromUserView,
    AssignPermissionToRoleView,
    RemovePermissionFromRoleView,
    UserRolesView,
    RolePermissionsView
    )


# ROUTER POUR LES VIEWSETS
# r indique que c'est une rawstring. ne traite pas les / comme des caractères spéciaux. 
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')


# URLS POUR LES API VIEWS

urlpatterns = [
    path('', include(router.urls)),  # inclut toutes les routes(router) CRUD Role & Permission
    
    # Assign / Remove Role to User
    path('user/assign-role/', AssignRoleToUserView.as_view(), name='assign-role'),
    path('user/remove-role/', RemoveRoleFromUserView.as_view(), name='remove-role'),

    # Assign / Remove Permission to Role
    path('role/assign-permission/', AssignPermissionToRoleView.as_view(), name='assign-permission'),
    path('role/remove-permission/', RemovePermissionFromRoleView.as_view(), name='remove-permission'),

    # Get roles of a user
    path('user/<int:user_id>/roles/', UserRolesView.as_view(), name='user-roles'),

    # Get permissions of a role
    path('role/<str:role_code>/permissions/', RolePermissionsView.as_view(), name='role-permissions'),
]