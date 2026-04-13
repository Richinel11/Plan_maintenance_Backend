from rest_framework import serializers
from .models import Utilisateur, EntiteMetier
from security.serializers import RoleSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EntiteMetierSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntiteMetier
        fields = '__all__'


class UtilisateurSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    entite_metier = EntiteMetierSerializer(read_only=True)

    class Meta:
        model = Utilisateur
        fields = '__all__'

class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class ToggleStatusSerializer(serializers.Serializer):
    pass  # pas de body
        
class CustomTokenSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["id"] = str(user.id)

        # supprimer user_id si présent
        
        if "user_id" in token:
            del token["user_id"]

        return token