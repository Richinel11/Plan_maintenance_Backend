from venv import logger

from rest_framework import serializers
from security.models import UserRole
from security.serializers import RoleSerializer
from .models import Utilisateur, EntiteMetier
from django.contrib.auth.hashers import make_password, check_password
from utils import LDAP_connect 
from rest_framework_simplejwt.tokens import RefreshToken
import logging

Logger = logging.getLogger(__name__)

class EntiteMetierSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntiteMetier
        fields = '__all__'


class UtilisateurSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    entite_metier = EntiteMetierSerializer(many =True, read_only =True)

    class Meta:
        model = Utilisateur
        fields = ['id','username', 'first_name', 'last_name', 'email',  'is_active', 'is_ldap', 'roles', 'entite_metier','first_connection', 'region']

    def get_roles(self, obj):
        # Récupère les roles de l'utilisateur via UserRole
        user_roles = UserRole.objects.filter(user=obj).select_related('role')
        roles = [ur.role for ur in user_roles]
        return RoleSerializer(roles, many=True).data
    
class UtilisateurUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'first_connection',
            'is_ldap',
            'region',
            'entite_metier',
        ]

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        username = attrs['username']
        password = attrs['password']

        if not username.isalnum():
            raise serializers.ValidationError("Username doit être alphanumérique")

        try:
            user = Utilisateur.objects.get(username=username)
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError("Identifiants invalides")
        if user.is_active == False:
            raise serializers.ValidationError("account blocked")
        if user.is_deleted == True:
            raise serializers.ValidationError("user does not exist")

        if user.is_ldap:
            try:
                LDAP_connect.ldap_login(username, password)
                logger.info("LDAP Auth OK pour %s", username)
            except Exception as e:
                logger.warning("Échec LDAP pour %s : %s", username, str(e))
                raise serializers.ValidationError("Identifiants invalides")
        else:
            if not check_password(password, user.password):
                raise serializers.ValidationError("Identifiants invalides")

        refresh = RefreshToken()
        refresh['user_id'] = str(user.id)
        
        access = refresh.access_token
        access['user_id'] = str(user.id)
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

class LoginResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField()
    ldap_dn = serializers.CharField(allow_blank=True)
    ldap_groups = serializers.ListField(child=serializers.CharField())
    first_password_change_required = serializers.BooleanField(default=False)
    region = serializers.CharField(allow_blank=True)
   
    
class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class ToggleStatusSerializer(serializers.Serializer):
    pass  
        