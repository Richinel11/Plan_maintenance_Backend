from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from drf_spectacular.utils import extend_schema, extend_schema_view
from user.models import Utilisateur
from .models import Role, Permission, UserRole, RolePermission
from .serializers import AssignPermissionSerializer, AssignRoleSerializer, RoleSerializer, PermissionSerializer
from .permission import HasPermission , HasPermissionFactory
from .services import (
    assign_role_to_user,
    remove_role_from_user,
    assign_permission_to_role,
    remove_permission_from_role,
    get_user_roles,
    get_role_permissions
)
from rest_framework.decorators import api_view, permission_classes


@extend_schema_view(
    list=extend_schema(tags=['Security'], description='Lister tous les rôles'),
    retrieve=extend_schema(tags=['Security'], description='Détail d’un rôle'),
    create=extend_schema(tags=['Security'], description='Créer un rôle'),
    update=extend_schema(tags=['Security'], description='Mettre à jour un rôle'),
    destroy=extend_schema(tags=['Security'], description='Supprimer un rôle'),
)

# create role
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_ROLES')])
def create_role (request):
    if request.method == 'POST' :
        Role.objects.create(
            nom = request.data["nom_role"],
            code_role = request.data["code_role"],
            description = request.data["description"]
        )
        return Response({'message': 'Role Created'}, status=status.HTTP_201_CREATED)
    return Response({'Error': 'Method not Allowed'}, status=status.HTTP_400_BAD_REQUEST)

#list roles
@api_view(['GET'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_ROLES')])
def get_role(request):
    role = Role.objects.all()
    serializer = RoleSerializer(role, many = True)
    if serializer.is_valid :
        return Response(serializer.data)
    
#update role
@api_view(['GET','PUT', "DELETE"])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_ROLES')])
def get_update_role(request, code_role):
    try:
        role = Role.objects.get(code_role = code_role )   
        
        if request.method == 'GET' :
            serializer = RoleSerializer(role, many = False)
            return Response(serializer.data) 
        
        if request.method == 'PUT':
            role.code_role = request.data['code_role']
            role.nom = request.data['nom']
            role.description = request.data['description']
            
            role.save()
            return Response({"message":"Role Updated"}, status=status.HTTP_200_OK) 
        
        # if request.method == 'DELETE':
        #     role.is_actif =False
        #     role.save()
        #     return Response({"message":"Role Deleted"}, status=status.HTTP_200_OK) 
    except Exception as e :
        return Response({"Error" : "Role not found"}, status=status.HTTP_400_BAD_REQUEST)

# PERMISSION CRUD

#list permissions
@api_view(['GET'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_PERMISSIONS')])
def get_permission(request):
    permisssion = Permission.objects.all()
    serializer = PermissionSerializer(permisssion, many = True)
    if serializer.is_valid :
        return Response(serializer.data)

#create permission
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_PERMISSIONS')])
def create_permission(request):
    if request.method == 'POST' :
        Permission.objects.create(
            nom = request.data["nom_permission"],
            code = request.data["code_permission"],
            description = request.data["description"]
        )
        return Response({'message': 'Permission Created'}, status=status.HTTP_201_CREATED)
    return Response({'Error': 'Method not Allowed'}, status=status.HTTP_400_BAD_REQUEST)

#update permissions
@api_view(['GET','PUT'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_PERMISSIONS')])
def get_update_permission(request, code_permission):
    try:
        permisison = Permission.objects.get(code = code_permission )   
        
        if request.method == 'GET' :
            serializer = PermissionSerializer(permisison, many = False)
            return Response(serializer.data) 
        
        if request.method == 'PUT':
            permisison.code = request.data['code_permission']
            permisison.nom = request.data['nom']
            permisison.description = request.data['description']
            
            permisison.save()
            return Response({"message":"Permission Updated"}, status=status.HTTP_200_OK) 
        
    except Exception as e :
        return Response({"Error" : "permission not found"}, status=status.HTTP_400_BAD_REQUEST)
        

#  Assigner un role a un utilisateur
class AssignRoleToUserView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["MANAGE_ROLES"]

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
    required_permissions = ["MANAGE_ROLES"]

    def post(self, request):
        user_id = request.data.get("user_id")
        role_code = request.data.get("role_code")

        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND)

        success = remove_role_from_user(user, role_code)

        if not success:
            return Response({"error": "Rôle introuvable"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Rôle retiré avec succès"})

#  Assigner un role a une permission
class AssignPermissionToRoleView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["MANAGE_PERMISSIONS"]

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
    required_permissions = ["MANAGE_PERMISSIONS"]

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
    required_permissions = ["MANAGE_PERMISSIONS"]

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
    required_permissions = ["MANAGE_PERMISSIONS"]

    def get(self, request, role_code):
        permissions = get_role_permissions(role_code)
        serializer = PermissionSerializer(permissions, many=True)

        return Response(serializer.data)
        
        