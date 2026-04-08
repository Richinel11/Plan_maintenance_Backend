from rest_framework import serializers 
from .models import Troncon, ReferenceReseau, Depart, Localisation, Poste, Ouvrage

class ReferenceReseauSerializer(serializers.ModelSerializer):
    
   
    #  écriture (POST)
    ouvrage = serializers.PrimaryKeyRelatedField(queryset=Ouvrage.objects.all())
    poste = serializers.PrimaryKeyRelatedField(queryset=Poste.objects.all())
    depart = serializers.PrimaryKeyRelatedField(queryset=Depart.objects.all())
    troncon = serializers.PrimaryKeyRelatedField(queryset=Troncon.objects.all())
    localisation = serializers.PrimaryKeyRelatedField(queryset=Localisation.objects.all())

    class Meta:
        model= ReferenceReseau
        fields = '__all__'
        
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