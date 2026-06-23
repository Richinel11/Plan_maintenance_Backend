from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Centrale, TypeReferentiel, Reference, ReferentielItem, Region
from .serializers import CentraleSerializer, TypeReferentielSerializer, ReferenceSerializer, ReferentielItemSerializer, RegionSerializer

_TAG = dict(
    list=extend_schema(tags=["Referentiel"]),
    create=extend_schema(tags=["Referentiel"]),
    retrieve=extend_schema(tags=["Referentiel"]),
    update=extend_schema(tags=["Referentiel"]),
    partial_update=extend_schema(tags=["Referentiel"]),
    destroy=extend_schema(tags=["Referentiel"]),
)


@extend_schema_view(**_TAG)
class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all().order_by('code')
    serializer_class = RegionSerializer


@extend_schema_view(**_TAG)
class CentraleViewSet(viewsets.ModelViewSet):
    queryset = Centrale.objects.all().order_by('valeur')
    serializer_class = CentraleSerializer


@extend_schema_view(**_TAG)
class TypeReferentielViewSet(viewsets.ModelViewSet):
    queryset = TypeReferentiel.objects.all().order_by('nom')
    serializer_class = TypeReferentielSerializer


_REFERENCE_TAG = dict(
    create=extend_schema(tags=["Referentiel"]),
    retrieve=extend_schema(tags=["Referentiel"]),
    update=extend_schema(tags=["Referentiel"]),
    partial_update=extend_schema(tags=["Referentiel"]),
    destroy=extend_schema(tags=["Referentiel"]),
    list=extend_schema(
        tags=["Referentiel"],
        summary="Lister les références",
        description=(
            "Retourne la liste de toutes les références avec leurs items.\n\n"
            "Utilisez `entite_metier_id` pour filtrer par entité métier "
            "et/ou `region_id` pour filtrer par région.\n\n"
            "**Exemple :** `GET /referentiel/references/?region_id=<uuid>`"
        ),
        parameters=[
            OpenApiParameter(
                name='entite_metier_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID de l'entité métier (Production, Transport, Distribution).",
            ),
            OpenApiParameter(
                name='region_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID de la région. Filtre les références appartenant à cette région.",
            ),
        ],
    ),
)


@extend_schema_view(**_REFERENCE_TAG)
class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = Reference.objects.select_related('entite_metier').prefetch_related('items__type').all()
    serializer_class = ReferenceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        INVALIDES = {'undefined', 'null', ''}

        entite_id = self.request.query_params.get('entite_metier_id')
        if entite_id and entite_id not in INVALIDES:
            qs = qs.filter(entite_metier_id=entite_id)

        region_id = self.request.query_params.get('region_id')
        if region_id and region_id not in INVALIDES:
            qs = qs.filter(region_id=region_id)

        return qs

    @extend_schema(tags=["Referentiel"], responses=ReferentielItemSerializer(many=True))
    @action(detail=True, methods=['get'], url_path='items')
    def items(self, request, pk=None):
        reference = get_object_or_404(Reference, pk=pk)
        items = ReferentielItem.objects.select_related('type').filter(reference=reference)
        serializer = ReferentielItemSerializer(items, many=True)
        return Response(serializer.data)


@extend_schema_view(**_TAG)
class ReferentielItemViewSet(viewsets.ModelViewSet):
    queryset = ReferentielItem.objects.select_related('type', 'reference').all()
    serializer_class = ReferentielItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        reference_id = self.request.query_params.get('reference_id')
        type_id = self.request.query_params.get('type_id')
        if reference_id:
            qs = qs.filter(reference_id=reference_id)
        if type_id:
            qs = qs.filter(type_id=type_id)
        return qs
