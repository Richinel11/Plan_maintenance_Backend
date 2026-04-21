from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view,permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Utilisateur
from .models import Utilisateur, EntiteMetier
from security.models import Role, UserRole
from .serializers import  SetPasswordSerializer, UtilisateurSerializer,  EntiteMetierSerializer, UtilisateurUpdateSerializer
from .serializers import LoginSerializer
from django.contrib.auth import authenticate
from utils import LDAP_connect 
import uuid 

from rest_framework_simplejwt.tokens import RefreshToken

@extend_schema_view(
    list=extend_schema(tags=['User'], description="Lister les utilisateurs"),
    retrieve=extend_schema(tags=['User'], description="Détail d’un utilisateur"),
    create=extend_schema(tags=['User'], description="Créer un utilisateur"),
    update=extend_schema(tags=['User'], description="Mettre à jour un utilisateur"),
    destroy=extend_schema(tags=['User'], description="Supprimer un utilisateur"),
    # actions custom
    toggle_status=extend_schema(tags=['User'], description="Activer / désactiver un utilisateur", responses={"200": {"actif": True}}),
    set_password=extend_schema(tags=['User'], request=SetPasswordSerializer, description="Changer le mot de passe"),
)




@api_view(['POST'])
def create_user(request):
    
    try: 
        role = Role.objects.get(code_role = request.data['code_role'])
        user = Utilisateur.objects.create(
            username = request.data['username'],
            first_name = request.data['first_name'],
            last_name = request.data['last_name'],
            email = request.data['email'],
            password = request.data['password'],
            first_connection = True,
            is_ldap = request.data['is_ldap']
        )
        UserRole.objects.create(
            user = user,
            role = role
        )
        
        return Response({"message" :"User ok"}, status=status.HTTP_201_CREATED)
    
    except Role.DoesNotExist: 
        return Response({'Error':'Role non existant'}, status=status.HTTP_400_BAD_REQUEST)

# list all user

@api_view(['GET'])
def get_users(request):
    # if not request.user.is_authenticated:
    #     return Response(
    #         {'error': 'Authentification requise'}, 
    #         status=status.HTTP_401_UNAUTHORIZED)

    users = Utilisateur.objects.filter(is_deleted = False)
    serializer = UtilisateurSerializer(users, many = True)
    if serializer.is_valid():
        return Response(serializer.data) 
    
# get update & delete  user
@api_view(['GET','PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_user_id(request, user_id):
    print(f"user id: {user_id}")
    return Response({"Respose ok"})



@api_view(['GET','PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_update_user(request, user_id):
    try:
        # print(f'{user_id}')
       
        user = Utilisateur.objects.get(id =user_id)
    except Utilisateur.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        print('get user by id')
        serializer = UtilisateurSerializer(user, many= False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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

    return Response({"message": "User updated"}, status=status.HTTP_200_OK)

    
# delete user
@api_view(['DELETE'])    
def delete_user(request, user_id):
    try:    
        user = Utilisateur.objects.get(id=user_id)
        user.is_deleted = True
        user.is_active = False
        user.deleted_at = timezone.now()
        user.save()
        return Response({"message": "User deleted"}, status=status.HTTP_204_NO_CONTENT)

    except Utilisateur.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    
    
#restauration d'un utilisateur
@api_view(['PATCH'])
def restore_user(request, user_id):
    try:
        user = Utilisateur.objects.get(id=user_id)
          
        if not user.is_deleted:
            return Response({'error': 'Cet utilisateur n\'est pas supprimé'},status=status.HTTP_400_BAD_REQUEST) 

        user.is_deleted = False
        user.deleted_at = None
        user.save()

        return Response({'message': 'Utilisateur restauré avec succès'},status=status.HTTP_200_OK)

    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'},status=status.HTTP_404_NOT_FOUND)

    #login api
class LoginAPIView(APIView):
    """
    API endpoint pour l'authentification des utilisateurs
    Supporte l'authentification locale et LDAP
    """
    permission_classes = []  # Pas d'authentification requise pour le login
    authentication_classes = []  # Pas d'authentification requise pour le login
    
    def post(self, request) :
        username = request.data["username"]
        password = request.data["password"]
        try: 
            user = Utilisateur.objects.get(username=username)
            
        except Utilisateur.DoesNotExist:
            print("step 1")
            return Response({"error":"user does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_active == False:
            print("step 2")
            return Response({"error":"account blocked"}, status=status.HTTP_400_BAD_REQUEST)
          
        if user.is_deleted == True:
            print("step 3")
            return Response({"error":"user does not exist"}, status=status.HTTP_400_BAD_REQUEST)
           
        if user.is_ldap :
            try:
                print("step 4")
                LDAP_connect.ldap_login(username, password)
                # logger.info("LDAP Auth OK pour %s", username)
            except Exception as e:
                # logger.warning("Échec LDAP pour %s : %s", username, str(e))
                return Response({"error":"Invalid username and password"}, status=status.HTTP_400_BAD_REQUEST)
                
        else:
            auth = authenticate(username=username , password=password)
            print("step 5")
            if auth is None :
                return Response({"error":"Invalid username and password"}, status=status.HTTP_400_BAD_REQUEST)
            print("step 6")     
        refresh = RefreshToken.for_user(user)
        print("step 7")

        return Response ({
            "user_id" : str(user.id),
            "access" :  str(refresh.access_token),
            "refresh" :  str(refresh)
        })
        
    # def post(self, request):
    #     # Validation des données d'entrée
    #     serializer = LoginSerializer(data=request.data)
        
    #     if serializer.is_valid():
    #         data =  serializer.validated_data
    #         return Response({
    #             'access' : data['access'],
    #             'refresh' : data['refresh']
    #         }, status=status.HTTP_200_OK)
            
    #   return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutAPIView(APIView):
    """Déconnexion de l'utilisateur"""
    
    def post(self, request):
        # Vider la session
        request.session.flush()
        return Response({'success': True,'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)



# class CustomAuthToken(ObtainAuthToken):
#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         token, created = Token.objects.get_or_create(user=user)
        
#         # Ajouter les infos supplémentaires
#         return Response({
#             'token': token.key,
#             'user_id': user.pk,
#             'username': user.username,
#             'role': user.role.nom if hasattr(user, 'role') else None
#         })
        
        

@extend_schema_view(
    list=extend_schema(tags=['User'], description="Lister les entités métier"),
    retrieve=extend_schema(tags=['User'], description="Détail d’une entité métier"),
    create=extend_schema(tags=['User'], description="Créer une entité métier"),
    update=extend_schema(tags=['User'], description="Mettre à jour une entité métier"),
    destroy=extend_schema(tags=['User'], description="Supprimer une entité métier"),
)

class EntiteMetierViewSet(ModelViewSet):
    queryset = EntiteMetier.objects.all()
    serializer_class = EntiteMetierSerializer