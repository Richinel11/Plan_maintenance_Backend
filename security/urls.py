from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssignRoleToUserView,
    RemoveRoleFromUserView,
    AssignPermissionToRoleView,
    RemovePermissionFromRoleView,
    UserRolesView,
    RolePermissionsView,
    
    create_role, get_role, get_update_role, create_permission, get_permission, get_update_permission
    )

# URLS POUR LES API VIEWS

urlpatterns = [
    
    path('roles/all-roles', get_role, name="get-all-role"),
    path('roles/create-role', create_role, name="create-new-role"),
    path('roles/update-role', get_update_role, name="update-role"),
    path('permissions/all-permission', get_permission, name="get-all-permission"),
    path('permissions/create-permission', create_permission, name="create-new-permission"),
    path('permissions/update-permission', get_update_permission, name="update-permission"),

    # Assign / Remove Role to User
    path('user/assign-role', AssignRoleToUserView.as_view(), name='assign-role'),
    path('user/remove-role', RemoveRoleFromUserView.as_view(), name='remove-role'),

    # Assign / Remove Permission to Role
    path('roles/assign-permission', AssignPermissionToRoleView.as_view(), name='assign-permission'),
    path('roles/remove-permission', RemovePermissionFromRoleView.as_view(), name='remove-permission'),

    # Get roles of a user
    path('user/<uuid:user_id>/roles', UserRolesView.as_view(), name='user-roles'),

    # Get permissions of a role
    path('roles/<str:role_code>/permissions', RolePermissionsView.as_view(), name='role-permissions'),
]