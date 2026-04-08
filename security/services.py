from django.db.models import Prefetch
from .models import Role, Permission, UserRole, RolePermission


# Fonctions concernant les PERMISSIONS des utilisateurs


def user_has_permission(user, permission_code):
    

   # Vérifie si un utilisateur possède une permission donnée via ses rôles


    if not user or not user.is_authenticated:
        return False

    # Super admin → accès total
    if user.is_superuser:
        return True

    return Permission.objects.filter(rolepermission__role__userrole__user=user, code=permission_code).exists()


def user_has_all_permissions(user, permission_codes: list):

    #Vérifie si l'utilisateur possède TOUTES les permissions
    
    for code in permission_codes:
        if not user_has_permission(user, code):
            return False
    return True


def user_has_any_permission(user, permission_codes: list):

   # Vérifie si l'utilisateur possède AU MOINS une permission

    for code in permission_codes:
        if user_has_permission(user, code):
            return True
    return False



#  Utilisateur <-> Role

def assign_role_to_user(user, role_code):

    #Assigner un rôle à un utilisateur
    try:
        role = Role.objects.get(code_role=role_code)
        UserRole.objects.get_or_create(user=user, role=role)
        return True
    except Role.DoesNotExist:
        return False


def remove_role_from_user(user, role_code):

    #Retirer un rôle à un utilisateur

    try:
        role = Role.objects.get(code_role=role_code)
        UserRole.objects.filter(user=user, role=role).delete()
        return True
    except Role.DoesNotExist:
        return False


def get_user_roles(user):

    #Retourne tous les rôles d’un utilisateur

    return Role.objects.filter(userrole__user=user)



# relations entre ROLE et PERMISSION

def assign_permission_to_role(role_code, permission_code):

   # Assigner une permission à un rôle

    try:
        role = Role.objects.get(code_role=role_code)
        permission = Permission.objects.get(code=permission_code)

        RolePermission.objects.get_or_create(
            role=role,
            permission=permission
        )
        return True

    except (Role.DoesNotExist, Permission.DoesNotExist):
        return False


def remove_permission_from_role(role_code, permission_code):

    #Retirer une permission d’un rôle

    try:
        role = Role.objects.get(code_role=role_code)
        permission = Permission.objects.get(code=permission_code)

        RolePermission.objects.filter(
            role=role,
            permission=permission
        ).delete()

        return True

    except (Role.DoesNotExist, Permission.DoesNotExist):
        return False


def get_role_permissions(role_code):

    #Retourne toutes les permissions d’un rôle
    
    return Permission.objects.filter(
        rolepermission__role__code_role=role_code
    )


# OPTIMISATION (optionnel mais puissant)


def get_user_permissions_optimized(user):
    
    #Retourne toutes les permissions d’un utilisateur (optimisé)

    roles = Role.objects.filter(userrole__user=user).prefetch_related(
        Prefetch(
            'role_permissions',queryset=RolePermission.objects.select_related(
                'permission')))

    permissions = []

    for role in roles:
        for rp in role.role_permissions.all():
            permissions.append(rp.permission.code)

    return list(set(permissions))