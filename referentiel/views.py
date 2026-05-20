from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema
from .models import Centrale, TypeReferentiel, Reference, ReferentielItem
from .serializers import CentraleSerializer, TypeReferentielSerializer, ReferenceSerializer, ReferentielItemSerializer

_TAG = dict(
    list=extend_schema(tags=["Referentiel"]),
    create=extend_schema(tags=["Referentiel"]),
    retrieve=extend_schema(tags=["Referentiel"]),
    update=extend_schema(tags=["Referentiel"]),
    partial_update=extend_schema(tags=["Referentiel"]),
    destroy=extend_schema(tags=["Referentiel"]),
)


@extend_schema_view(**_TAG)
class CentraleViewSet(viewsets.ModelViewSet):
    queryset = Centrale.objects.all().order_by('nom')
    serializer_class = CentraleSerializer


@extend_schema_view(**_TAG)
class TypeReferentielViewSet(viewsets.ModelViewSet):
    queryset = TypeReferentiel.objects.all().order_by('nom')
    serializer_class = TypeReferentielSerializer


@extend_schema_view(**_TAG)
class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = Reference.objects.prefetch_related('items__type').all()
    serializer_class = ReferenceSerializer

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
