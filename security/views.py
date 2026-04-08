from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from user.models import Utilisateur
from .models import Role, Permission, UserRole, RolePermission
from .serializers import RoleSerializer, PermissionSerializer, UserRoleSerializer, RolePermissionSerializer
from .permission import HasPermission
from .services import (
    assign_role_to_user,
    remove_role_from_user,
    assign_permission_to_role,
    remove_permission_from_role,
    get_user_roles,
    get_role_permissions
)

from django.contrib.auth import get_user_model


#  ROLE CRUD

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["manage_roles"]

# PERMISSION CRUD


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["manage_permissions"]


#  Assigner un role a un utilisateur

class AssignRoleToUserView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["assign_role"]

    def post(self, request):
        user_id = request.data.get("user_id")
        role_code = request.data.get("role_code")

        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND)

        success = assign_role_to_user(user, role_code)

        if not success:
            return Response({"error": "Rôle introuvable"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Rôle assigné avec succès"})


#  retirer un role a un utilisateur

class RemoveRoleFromUserView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["assign_role"]

    def post(self, request):
        user_id = request.data.get("user_id")
        role_code = request.data.get("role_code")

        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=404)

        success = remove_role_from_user(user, role_code)

        if not success:
            return Response({"error": "Rôle introuvable"}, status=400)

        return Response({"message": "Rôle retiré avec succès"})


#  Assigner un role a une permission

class AssignPermissionToRoleView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["assign_permission"]

    def post(self, request):
        role_code = request.data.get("role_code")
        permission_code = request.data.get("permission_code")

        success = assign_permission_to_role(role_code, permission_code)

        if not success:
            return Response(
                {"error": "Rôle ou permission introuvable"},
                status=400
            )

        return Response({"message": "Permission assignée au rôle"})


# retirer une permission d'un role

class RemovePermissionFromRoleView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["assign_permission"]

    def post(self, request):
        role_code = request.data.get("role_code")
        permission_code = request.data.get("permission_code")

        success = remove_permission_from_role(role_code, permission_code)

        if not success:
            return Response(
                {"error": "Rôle ou permission introuvable"},
                status=400
            )

        return Response({"message": "Permission retirée du rôle"})


# afficher ler roles d'un utilisateur

class UserRolesView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["view_roles"]

    def get(self, request, user_id):
        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND)

        roles = get_user_roles(user)
        serializer = RoleSerializer(roles, many=True)

        return Response(serializer.data)


#  voir les permissions par roles

class RolePermissionsView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["view_permissions"]

    def get(self, request, role_code):
        permissions = get_role_permissions(role_code)
        serializer = PermissionSerializer(permissions, many=True)

        return Response(serializer.data)
        
