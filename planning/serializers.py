# planing/serializers.py
from rest_framework import serializers
from .models import PlanningTravaux, TypeActivite
from user.models import Utilisateur
from referentiel.models import ReferenceReseau
from referentiel.serializers import ReferenceReseauSerializer


        
class TypeActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeActivite
        fields = ['id', 'libelle']

class UtilisateurShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'first_name', 'last_name']


class PlanningTravauxSerializer(serializers.ModelSerializer):

    # READ : retourne les objets complets
    type_activite = TypeActiviteSerializer(read_only=True)
    cree_par = UtilisateurShortSerializer(read_only=True)
    modifie_par = UtilisateurShortSerializer(read_only=True)
    reference = ReferenceReseauSerializer(read_only=True)

    # WRITE : accepte les IDs
    type_activite_id = serializers.PrimaryKeyRelatedField(queryset=TypeActivite.objects.all(), source='type_activite', write_only=True)
    cree_par_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all(), source='cree_par', write_only=True)
    modifie_par_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all(), source='modifie_par', write_only=True)
    reference_id = serializers.SlugRelatedField(
        queryset=ReferenceReseau.objects.all(),source='reference', slug_field='code_reference', write_only=True)

    class Meta:
        model = PlanningTravaux
        fields = [
            'id', 'titre', 'observation', 'statut_travaux',
            'jour_debut_planifie', 'duree_planifiee', 'jour_fin_planifie',
            # read
            'reference', 'type_activite', 'cree_par', 'modifie_par',
            # write
            'reference_id', 'type_activite_id', 'cree_par_id', 'modifie_par_id',
        ]
# class reporterSerializer(serializers.Serializer):
#     date_report_travaux = serializers.DateField(required= True)
    
