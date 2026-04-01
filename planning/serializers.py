# planing/serializers.py
from rest_framework import serializers
from .models import PlanningTravaux, TypeActivite
from user.models import Utilisateur
from referentiel.models import ReferenceReseau

class PlanningTravauxSerializer(serializers.ModelSerializer):
    # On peut ajouter des champs liés à l'affichage
    type_activite_libelle = serializers.CharField(source='type_activite.libelle', read_only=True)
    reference_libelle = serializers.CharField(source='reference.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.username', read_only=True)
    modifie_par_nom = serializers.CharField(source='modifie_par.username', read_only=True)
    
    class Meta:
        model = PlanningTravaux
        fields = '__all__'

class TypeActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeActivite
        fields = '__all__'