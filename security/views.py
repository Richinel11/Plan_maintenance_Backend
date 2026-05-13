from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from user.models import Utilisateur
from .models import Role, Permission, UserRole, RolePermission
from .serializers import (
    RoleSerializer, PermissionSerializer, UpdateUserRoleSerializer,
    AssignRoleSerializer, AssignPermissionSerializer,
    CreateRoleSerializer, UpdateRoleSerializer,
    CreatePermissionSerializer, UpdatePermissionSerializer,
)
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
from drf_spectacular.utils import extend_schema


# create role
@extend_schema(
    tags=["Security"],
    request=CreateRoleSerializer,
    responses={201: {"type": "object"}, 400: {"type": "object"}},
    description="Créer un nouveau rôle"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_ROLES')])
def create_role (request):
    if request.method == 'POST' :
        Role.objects.create(
            nom = request.data["nom_role"],
            code_role = request.data["code_role"],
            description = request.data["description"]
        )
        return Response({
            "message-en": "role Created",
            "message": 'role Crée'
        },status=status.HTTP_201_CREATED)
    return Response({
        "error-en": 'Only Method POST is Allowed',
        "error-fr": "seule la méthode POST est autorisée"
    },status=status.HTTP_400_BAD_REQUEST)

#list roles
@extend_schema(
    tags=["Security"],
    responses={200: RoleSerializer(many=True)},
    description="Lister tous les rôles"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_ROLES')])
def get_role(request):
    role = Role.objects.all()
    serializer = RoleSerializer(role, many = True)
    if serializer.is_valid :
        return Response(serializer.data)
    
#update role
@extend_schema(
    tags=["Security"],
    request=UpdateRoleSerializer,
    responses={200: {"type": "object"}, 400: {"type": "object"}},
    description="Récupérer ou mettre à jour un rôle par son code"
)
@api_view(['GET','PUT'])
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
            return Response({"error-en":"Role Updated",
                             "error-fr":"Role mis à jour"},
                            status=status.HTTP_200_OK) 
     
    except Exception as e :
        return Response({"error-en" : "Role not found",
                         "error-fr":"Role introuvable"},
                        status=status.HTTP_400_BAD_REQUEST)
    
    
#supprimer un role
@extend_schema(
    tags=["Security"],
    responses={204: None, 404: {"type": "object"}},
    description="Supprimer un rôle"
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, HasPermissionFactory('DELETE_ROLES')])

def delete_role(request, code_role):
    try:
        
        role = Role.objects.get(code_role=code_role)
    except Role.DoesNotExist:
        return Response (
            {'error-fr': 'le role n\'existe pas',
             'error-en':'role does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
    role.delete()
    
    return Response({'message-fr':'role supprimer',
                     'message-en': 'role deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
# PERMISSION CRUD

#list permissions
@extend_schema(
    tags=["Security"],
    responses={200: PermissionSerializer(many=True)},
    description="Lister toutes les permissions"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_PERMISSIONS')])
def get_permission(request):
    permisssion = Permission.objects.all()
    serializer = PermissionSerializer(permisssion, many = True)
    if serializer.is_valid :
        return Response(serializer.data)

#create permission
@extend_schema(
    tags=["Security"],
    request=CreatePermissionSerializer,
    responses={201: {"type": "object"}, 400: {"type": "object"}},
    description="Créer une nouvelle permission"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_PERMISSIONS')])
def create_permission(request):
    if request.method == 'POST' :
        Permission.objects.create(
            nom = request.data["nom_permission"],
            code = request.data["code_permission"],
            description = request.data["description"],
            module = request.data["module"]
        )
        return Response({'message': 'Permission Created'}, status=status.HTTP_201_CREATED)
    return Response({'Error': 'Method not Allowed'}, status=status.HTTP_400_BAD_REQUEST)

#update permissions
@extend_schema(
    tags=["Security"],
    request=UpdatePermissionSerializer,
    responses={200: {"type": "object"}, 400: {"type": "object"}},
    description="Récupérer ou mettre à jour une permission par son code"
)
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
            permisison.module = request.data['module']
            
            permisison.save()
            return Response({"error-en":"Permission Updated",
                             'error-fr':"permission mise-à-jour"},
                            status=status.HTTP_200_OK) 
        
    except Exception as e :
        return Response({"error-en" : "permission not found",
                         "error-fr":"permission introuvable"},
                        status=status.HTTP_400_BAD_REQUEST)
    
    
#supprimer une permission
@extend_schema(
    tags=["Security"],
    responses={204: None, 404: {"type": "object"}},
    description="Supprimer une permission"
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, HasPermissionFactory('DELETE_PERMISSIONS')])

def delete_permission(request, code_permission):
    try:
        
        permission = Permission.objects.get(code=code_permission)
    except Permission.DoesNotExist:
        return Response (
            {'error-fr': 'le permission n\'existe pas',
             'error-en':'permission does not exist'},
            status=status.HTTP_404_NOT_FOUND)
        
    permission.delete()
    
    return Response({'message-fr':'permission supprimer',
                     'message-en': 'permission deleted successfully'},
                    status=status.HTTP_204_NO_CONTENT)
        

#  Assigner un role a un utilisateur
class AssignRoleToUserView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["MANAGE_ROLES"]

    @extend_schema(
        tags=["Security"],
        request=AssignRoleSerializer,
        responses={200: {"type": "object"}, 400: {"type": "object"}, 404: {"type": "object"}},
        description="Assigner un rôle à un utilisateur"
    )
    def post(self, request):
        user_id = request.data.get("user_id")
        role_code = request.data.get("role_code")

        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({"error-fr": "Utilisateur introuvable",
                             "error-en":"user not found"},
                            status=status.HTTP_404_NOT_FOUND)

        success = assign_role_to_user(user, role_code)

        if not success:
            return Response({"error-fr": "Rôle introuvable",
                             "error-en": "Role not found"},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({"error-fr": "Rôle assigné avec succès",
                         "error-en":"Role assigned successfully"})


#modifier le role d'un utilisateur
@extend_schema(
    tags=["Security"],
    request=UpdateUserRoleSerializer,
    responses={200: {"type": "object"}, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Modifier le rôle assigné à un utilisateur"
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_ROLES')])
def update_user_role(request, user_id):
    #Récupérer l'utilisateur
    
    try:
        user = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        return Response({"error-fr": "Utilisateur introuvable",
                         "error-en":"User not found"},status=status.HTTP_404_NOT_FOUND)

    # Récupère le UserRole existant
    user_role = UserRole.objects.filter(user=user).first()

    if not user_role:
        return Response( {"error-fr": "Aucun rôle assigné à cet utilisateur",
                          "error-en":"User don't have any Role"},
                        status=status.HTTP_404_NOT_FOUND)

    serializer = UpdateUserRoleSerializer(user_role, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response( 
            {
                "error-fr": "Rôle mis à jour avec succès",
                "error-en": "Role updated successfully",
                "user": user.username,
                "role": user_role.role.code_role
            },status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#  retirer un role a un utilisateur
class RemoveRoleFromUserView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["MANAGE_ROLES"]

    @extend_schema(
        tags=["Security"],
        request=AssignRoleSerializer,
        responses={200: {"type": "object"}, 400: {"type": "object"}, 404: {"type": "object"}},
        description="Retirer un rôle d'un utilisateur"
    )
    def post(self, request):
        user_id = request.data.get("user_id")
        role_code = request.data.get("role_code")

        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({"error-fr": "Utilisateur introuvable",
                             "error-en": "user not found"},
                            status=status.HTTP_404_NOT_FOUND)

        success = remove_role_from_user(user, role_code)

        if not success:
            return Response({"error-fr": "Rôle introuvable",
                             "error-en":"Role not found"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error-fr": "Rôle retiré avec succès",
                         "error-en":"Role removed"}, status=status.HTTP_200_OK)

#  Assigner un role a une permission
class AssignPermissionToRoleView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permissions = ["MANAGE_PERMISSIONS"]

    @extend_schema(
        tags=["Security"],
        request=AssignPermissionSerializer,
        responses={200: {"type": "object"}, 400: {"type": "object"}},
        description="Assigner une permission à un rôle"
    )
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

    @extend_schema(
        tags=["Security"],
        request=AssignPermissionSerializer,
        responses={200: {"type": "object"}, 400: {"type": "object"}},
        description="Retirer une permission d'un rôle"
    )
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

    @extend_schema(
        tags=["Security"],
        responses={200: RoleSerializer(many=True), 404: {"type": "object"}},
        description="Afficher les rôles d'un utilisateur"
    )
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

    @extend_schema(
        tags=["Security"],
        responses={200: PermissionSerializer(many=True)},
        description="Voir les permissions d'un rôle"
    )
    def get(self, request, role_code):
        permissions = get_role_permissions(role_code)
        serializer = PermissionSerializer(permissions, many=True)

        return Response(serializer.data)
        
        