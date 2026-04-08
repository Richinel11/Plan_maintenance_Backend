# planing/serializers.py
from rest_framework import serializers
from .models import PlanningTravaux, TypeActivite
from user.models import Utilisateur
from referentiel.models import ReferenceReseau
from referentiel.serializers import ReferenceReseauSerializer


class PlanningTravauxSerializer(serializers.ModelSerializer):
    type_activite_libelle = serializers.CharField(source='type_activite.libelle', read_only=True)
    reference_libelle = serializers.CharField(source='reference.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.username', read_only=True)
    modifie_par_nom = serializers.CharField(source='modifie_par.username', read_only=True)
    reference = serializers.PrimaryKeyRelatedField(queryset=ReferenceReseau.objects.all())
    reference_detail = ReferenceReseauSerializer(source='reference', read_only=True)

  
    
    # Pour créer / mettre à jour via API, on passe juste les IDs
    
    type_activite = serializers.PrimaryKeyRelatedField(queryset=TypeActivite.objects.all())
    cree_par = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all())
    modifie_par = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all())
    reference = serializers.PrimaryKeyRelatedField(queryset=ReferenceReseau.objects.all())

    class Meta:
        model = PlanningTravaux
        fields = '__all__'
        
class reporterSerializer(serializers.Serializer):
    date_report_travaux = serializers.DateField(required= True)
    
        
class TypeActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeActivite
        fields = '__all__'