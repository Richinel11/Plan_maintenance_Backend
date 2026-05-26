from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view,permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Utilisateur, EntiteMetier, UniteDemanderesse
from security.models import Role, UserRole
from security.permission import HasPermissionFactory, is_admin
from .serializers import(
    CreateUserSerializer,
    SetPasswordSerializer,
    UtilisateurSerializer,
    EntiteMetierSerializer,
    UniteDemanderesseSerializer,
    UtilisateurUpdateSerializer,
    LoginSerializer,
)
from django.contrib.auth import authenticate
from utils import LDAP_connect 
from rest_framework_simplejwt.tokens import RefreshToken


@extend_schema(
    tags=["Users"],
    request=CreateUserSerializer,
    responses={201: {"type": "object"}, 400: {"type": "object"}, 500: {"type": "object"}},
    description="Créer un nouvel utilisateur avec rôle"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_USERS')])
def create_user(request):
    
    try:
        try: 
            role = Role.objects.get(code_role = request.data['code_role'])
        except Role.DoesNotExist: 
            return Response({
                'error-fr':'Role non existant',
                'error-en': 'this Role do not exist'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        user = Utilisateur.objects.create_user(
            username = request.data['username'],
            first_name = request.data['first_name'],
            last_name = request.data['last_name'],
            email = request.data['email'],
            password = request.data['password'],
            first_connection = True,
            is_ldap = request.data['is_ldap'],
            region = request.data.get('region', None),
            entite_metier = EntiteMetier.objects.get(id=request.data['entite_metier']) if request.data.get('entite_metier') else None
        )
        UserRole.objects.create(
            user = user,
            role = role
        )
        
        return Response({
            "error-en" :"User created",
            "error-fr":'Utilisateur crée'},
                        status=status.HTTP_201_CREATED)
    
    except Exception as e: 
        return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# list all user

@extend_schema(
    tags=["Users"],
    responses={200: UtilisateurSerializer(many=True)},
    description="Récupérer la liste de tous les utilisateurs"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_USERS')])
def get_users(request):
    # if not request.user.is_authenticated:
    #     return Response(
    #         {'error': 'Authentification requise'}, 
    #         status=status.HTTP_401_UNAUTHORIZED)

    users = Utilisateur.objects.filter(is_deleted = False)
    serializer = UtilisateurSerializer(users, many = True)
    if serializer.is_valid:
        return Response(serializer.data) 

# find user

@extend_schema(
    tags=["Users"],
    responses={200: UtilisateurSerializer, 404: {"type": "object"}},
    description="Récupérer les informations d'un utilisateur"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def find_user(request, user_id):
    try :
        user = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        return Response({
            'error-en': 'User does not exist',
            'error-fr': 'l\'utilisateur n\'exsite pas'},
                        status=status.HTTP_404_NOT_FOUND)
    
    serialzer =UtilisateurSerializer(user, many=False)
    return Response(serialzer.data, status=status.HTTP_200_OK)

# update user

@extend_schema(
    tags=["Users"],
    request=UtilisateurUpdateSerializer,
    responses={200: UtilisateurSerializer, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Mettre à jour les informations d'un utilisateur"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_USERS')])
def get_update_user(request, user_id):
    try:
        
        user = Utilisateur.objects.get(id =user_id)
    except Utilisateur.DoesNotExist:
        return Response({'error-en': 'User not found',
                         'error-fr':'l\'utilisateur n\'existe pas'},
                        status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        serializer = UtilisateurUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'PATCH':
    
        serializer = UtilisateurUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #Update role si fourni
    if request.data.get('code_role'):
       role = Role.objects.get(code_rol=request.data.get('code_role'))
       user_role = UserRole.objects.filter(user=user).first()

       if user_role:
          user_role.role = role
          user_role.save()
       else:
           UserRole.objects.create(user=user, role=role)

    return Response({"error-en": "User updated",
                     'error-fr': 'Utilisateur mis à jour'},
                    status=status.HTTP_200_OK)

    
# delete user (soft delete)
@extend_schema(
    tags=["Users"],
    responses={200: {"type": "object"}, 404: {"type": "object"}},
    description="Désactiver un utilisateur"
)
@api_view(['DELETE'])   
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_USERS')]) 
def delete_user(request, user_id):
    try:    
        user = Utilisateur.objects.get(id=user_id)
        user.is_active = False
        user.is_deleted = False
        user.save()
        return Response({
            "error-en": "User desactivated successfully",
            "error-fr": "utilisateur désactiver avec succes"},
                        status=status.HTTP_200_OK)

    except Utilisateur.DoesNotExist:
        return Response({'error-en': 'User not found',
                         'error-fr': 'l\'utilisateur n\'existe pas'},
                        status=status.HTTP_404_NOT_FOUND)
    
    
    
#restauration d'un utilisateur
@extend_schema(
    tags=["Users"],
    responses={200: {"type": "object"}, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Réactiver un utilisateur"
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated,HasPermissionFactory('MANAGE_USERS')])
def restore_user(request, user_id):
    try:
        user = Utilisateur.objects.get(id=user_id)
          
        if user.is_active:
            return Response({'error-fr': 'Cet utilisateur est déja actif',
                             'error-en':'User is already active'},
                            status=status.HTTP_400_BAD_REQUEST) 

        user.is_active = True #reactivation
        user.is_deleted = False
        user.save()

        return Response({'error-fr': 'Utilisateur restauré avec succès',
                         'error-en':'User reactvated successfully'},
                        status=status.HTTP_200_OK)

    except Utilisateur.DoesNotExist:
        return Response({'error-fr': 'Utilisateur non trouvé',
                         'error-en':'User not found'},
                        status=status.HTTP_404_NOT_FOUND)


# changer de password

@extend_schema(
    tags=["Users"],
    request=SetPasswordSerializer,
    responses={200: {"type": "object"}, 400: {"type": "object"}},
    description="Changer le mot de passe de l'utilisateur connecté"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user   
    new_password = request.data.get('new_password') 
    
    if not new_password:
        return Response({"error-fr": "mot de passe requis",
                         'error-en': 'password required'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    #controle sur la longueur du password
    if len(new_password) < 8:
        return Response({"error-fr": "mot de passe trop court.Au moins 8 caractères",
                         'error-en': 'short password! at least 8 characters'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    
    if hasattr(user, "first_connection"):
        user.first_connection = False
        
    user.save()
    
    return Response({"error-fr": "Mot de passe mis à jour avec succès!",
                     'error-en': 'password Updated!'},
                    status=status.HTTP_200_OK)



    #login api
class LoginAPIView(APIView):
    """
    API endpoint pour l'authentification des utilisateurs
    Supporte l'authentification locale et LDAP
    """
    permission_classes = []  # Pas d'authentification requise pour le login
    authentication_classes = []  # Pas d'authentification requise pour le login
    
    @extend_schema(
        tags=["Users"],
        request=LoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                    "user": {"type": "object"},
                    "first_connection": {"type": "boolean"},
                }
            }
        },
        description="Authentification utilisateur avec username et password"
    )
    def post(self, request) :
        username = request.data["username"]
        password = request.data["password"]

        if not username or not password:
            return Response(
                {'error-en':'username et password requis',
                 'error-fr':'non d\'utilisateur et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST)
            
        # Vérifier l'existence de l'utilisateur dans notre BD
        try: 
            user = Utilisateur.objects.get(username=username)
            
        except Utilisateur.DoesNotExist:
            
            return Response(
                {"error-en":"user does not exist",
                 'error-fr': 'l\'utilisateur n\'existe pas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifications de l'état du compte
        
        if user.is_active == False:
            
            return Response(
                {"error-en":"account blocked",
                 'error-fr': 'compte blocké'},
                status=status.HTTP_400_BAD_REQUEST
            )
          
        if user.is_deleted == True:
            
            return Response(
                {"error-en":"user does not exist",
                 'error-fr': 'l\'utilisateur n\'existe pas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #Authentification : LDAP ou locale 
          
        if user.is_ldap :
            # L'utilisateur est dans l'Active Directory -> on délègue l'auth à LDAP_connect
            try:
                
                LDAP_connect.ldap_login(username, password)
                #logger.info("LDAP Authentificationc  OK pour %s", username)
            except Exception as e:
                # logger.warning("Échec LDAP pour %s : %s", username, str(e))
                return Response({"error-en":"Invalid username and password",
                                 "error-fr":"mot-de-passe ou nom d\'utilisateur invalide"},
                                status=status.HTTP_400_BAD_REQUEST)
                
        else:
            # Authentification Django standard (password hashé en BD)
            auth = authenticate(username=username , password=password)
            
            if auth is None :
                return Response({"error-en":"Invalid username and password",
                                 "error-fr":"mot-de-passe ou nom d\'utilisateur invalide"},
                                status=status.HTTP_400_BAD_REQUEST)
                 
         # Mise à jour de la dernière connexion 
        user.last_connection_at = timezone.now()
        user.save(update_fields=['last_connection_at']) 
                
        # Génération des tokens JWT         
        refresh = RefreshToken.for_user(user)
    
        #Sérialisation des informations utilisateur (depuis notre BD)
        user_data = UtilisateurSerializer(user).data
        
        return Response ({
            "user_id" : str(user.id),
            "access" :  str(refresh.access_token),
            "user": user_data,
            "refresh" :  str(refresh),
            "first_connection" : user.first_connection,
        }, status=status.HTTP_200_OK)
    
class LogoutAPIView(APIView):
    """Déconnexion de l'utilisateur : blacklist du refresh token"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Users"],
        request={"type": "object", "properties": {"refresh": {"type": "string"}}},
        responses={200: {"type": "object", "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}}}},
        description="Déconnexion et blacklist du refresh token"
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception :
            pass # token déjà expiré ou invalide, on laisse passer
        #request.session.flush()
        return Response({'success': True,'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)


        
@extend_schema_view(
    list=extend_schema(tags=["Users"]),
    create=extend_schema(tags=["Users"]),
    retrieve=extend_schema(tags=["Users"]),
    update=extend_schema(tags=["Users"]),
    partial_update=extend_schema(tags=["Users"]),
    destroy=extend_schema(tags=["Users"]),
)
class EntiteMetierViewSet(ModelViewSet):
    queryset = EntiteMetier.objects.all()
    serializer_class = EntiteMetierSerializer


@extend_schema_view(
    list=extend_schema(tags=["Users"]),
    create=extend_schema(tags=["Users"]),
    retrieve=extend_schema(tags=["Users"]),
    update=extend_schema(tags=["Users"]),
    partial_update=extend_schema(tags=["Users"]),
    destroy=extend_schema(tags=["Users"]),
)
class UniteDemanderesseViewSet(ModelViewSet):
    queryset = UniteDemanderesse.objects.select_related('entite_metier').all().order_by('nom')
    serializer_class = UniteDemanderesseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        entite_id = self.request.query_params.get('entite_metier_id')
        if entite_id:
            qs = qs.filter(entite_metier_id=entite_id)
        if not is_admin(self.request.user):
            region = self.request.user.region
            if region:
                qs = qs.filter(region=region)
        return qs


@extend_schema(
    tags=["Users"],
    responses={200: UtilisateurSerializer(many=True)},
    description="Récupérer la liste des charges de consignation"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_charges_consignation(request):
    from security.models import UserRole
    user_roles = UserRole.objects.filter(role__code_role="CHARGE_CONSIGNATION").select_related('user')
    users = [ur.user for ur in user_roles if ur.user.is_active and not ur.user.is_deleted]
    serializer = UtilisateurSerializer(users, many=True)
    return Response(serializer.data)