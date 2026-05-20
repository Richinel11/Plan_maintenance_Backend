from rest_framework import serializers
from .models import Centrale, TypeReferentiel, Reference, ReferentielItem


class CentraleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centrale
        fields = '__all__'


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

    class Meta:
        model = Reference
        fields = ['id', 'valeur', 'items']
