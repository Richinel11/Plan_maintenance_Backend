from rest_framework import serializers
from .models import Centrale, TypeReferentiel, Reference, ReferentielItem
from user.models import EntiteMetier


class EntiteMetierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntiteMetier
        fields = ['id', 'name']


class CentraleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centrale
        fields = ['id', 'valeur']


class TypeReferentielSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeReferentiel
        fields = '__all__'


class ReferentielItemSerializer(serializers.ModelSerializer):
    type = TypeReferentielSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeReferentiel.objects.all(), source='type', write_only=True
    )

    class Meta:
        model = ReferentielItem
        fields = ['id', 'valeur', 'reference', 'type', 'type_id']


class ReferenceSerializer(serializers.ModelSerializer):
    items = ReferentielItemSerializer(many=True, read_only=True)
    entite_metier = EntiteMetierShortSerializer(read_only=True)
    entite_metier_id = serializers.PrimaryKeyRelatedField(
        queryset=EntiteMetier.objects.all(), source='entite_metier',
        write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Reference
        fields = ['id', 'valeur', 'entite_metier', 'entite_metier_id', 'items']
