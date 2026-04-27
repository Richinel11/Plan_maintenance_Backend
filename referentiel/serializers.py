from rest_framework import serializers 
from .models import Troncon, ReferenceReseau, Depart, Localisation, Poste, Ouvrage


class OuvrageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ouvrage
        fields = '__all__'
        
class TronconSerializer(serializers.ModelSerializer):
    class Meta:
        model = Troncon
        fields = '__all__'
        
class DepartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depart
        fields = '__all__'
        
        
class LocalisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localisation
        fields = '__all__'
        
class PosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = '__all__'
        
        

class ReferenceReseauSerializer(serializers.ModelSerializer):

    # READ : retourne les objets complets
    ouvrage = OuvrageSerializer(read_only=True)
    poste = PosteSerializer(read_only=True)
    depart = DepartSerializer(read_only=True)
    troncon = TronconSerializer(read_only=True)
    localisation = LocalisationSerializer(read_only=True)

    # WRITE : accepte les IDs
    ouvrage_id = serializers.PrimaryKeyRelatedField(queryset=Ouvrage.objects.all(), source='ouvrage', write_only=True)
    poste_id = serializers.PrimaryKeyRelatedField(
        queryset=Poste.objects.all(), source='poste',
        write_only=True, allow_null=True, required=False
)
    depart_id = serializers.PrimaryKeyRelatedField(
        queryset=Depart.objects.all(), source='depart',
        write_only=True, allow_null=True, required=False
    )
    troncon_id = serializers.PrimaryKeyRelatedField(
        queryset=Troncon.objects.all(), source='troncon',
        write_only=True, allow_null=True, required=False
    )
    localisation_id = serializers.PrimaryKeyRelatedField(queryset=Localisation.objects.all(), source='localisation', write_only=True)

    class Meta:
        model = ReferenceReseau
        fields = [
            'id', 'code_reference', 'libelle', 'actif',
            # read
            'ouvrage', 'poste', 'depart', 'troncon', 'localisation',
            # write
            'ouvrage_id', 'poste_id', 'depart_id', 'troncon_id', 'localisation_id',
        ]
        