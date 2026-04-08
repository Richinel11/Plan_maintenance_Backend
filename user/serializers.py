from rest_framework import serializers
from .models import Utilisateur, EntiteMetier
from security.serializers import RoleSerializer

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