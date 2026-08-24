from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .kpi_service import _get_poste_from_travail
from planning.models import Planning, Travail, PropositionAlignement
from .models import (
    Centrale,
    TypeReferentiel,
    Reference,
    ReferentielItem,
    Region,
    Troncon
)
from .serializers import(
    CentraleSerializer, TypeReferentielSerializer,
    ReferenceSerializer, ReferentielItemSerializer,
    RegionSerializer, TronconSerializer
)

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
    queryset = Centrale.objects.all().order_by('-date_creation')
    serializer_class = CentraleSerializer

@extend_schema_view(**_TAG)
class RegionViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset= Region.objects.all().order_by('code')
    serializer_class= RegionSerializer
    
    @extend_schema(
        tags=["KPI - Regions"],
        description=(
            "Retourne les plannings groupés par région électrique. "
            "Paramètre optionnel : ?region=DRY pour filtrer une région précise."
            )
    )
    @action(detail=False, methods=["GET"],  url_path='plannings')
    def plannings_par_region(self, request):
        """
        Retourne pour chaque région :
        - Le nombre de plannings
        - Le détail des plannings avec leur statut workflow courant
        """
        region_code = request.query_params.get('region')
        if region_code:
            self.queryset = self.queryset.filter(code=region_code)
        
        resultat = []
        
        for region in self.queryset:
            #Récupérer les plannings via les références de cette région
            planning_ids = Travail.objects.filter(
             reference__region=region
            ).values_list('planning_id', flat=True).distinct()
            
            plannings = Planning.objects.filter(
                id__in=planning_ids
            ).select_related('current_step', 'entite_metier', 'cree_par')
            
            resultat.append({
                "region": region.code,
                "total_plannings": plannings.count(),
                "plannings":[
                    {
                        "id": str(p.id),
                        "code": p.code,
                        "nom": p.nom,
                        "entite_metier": p.entite_metier.name if p.entite_metier else None,
                        "statut_workflow": p.current_step.name if p.current_step else None,
                        "step_code": p.current_step.code if p.current_step else None,
                        "date_creation": p.date_creation,
                    }
                    for p in plannings
                ]
            })
       
        return Response({
            "total_regions": len(resultat),
            "regions": resultat,
        }, status=status.HTTP_200_OK) 
    
    @extend_schema(
        tags=["KPI - Régions"],
        description=(
            "Retourne les propositions d'alignement groupées par type "
            "(DISTRIBUTION-DISTRIBUTION, TRANSPORT-TRANSPORT, DISTRIBUTION_POSTE_SOURCE) "
            "et par ouvrage. "
            "Paramètre optionnel : ?region=DRY"
        )
    )
    
    
    @action(detail=False, methods=['GET'], url_path='alignements')
    def alignements_par_type_et_ouvrage(self, request):
        """
        Trois catégories d'alignement :
        1. TRANSPORT ↔ TRANSPORT
        2. DISTRIBUTION ↔ DISTRIBUTION (lignes)
        3. DISTRIBUTION_POSTE_SOURCE ↔ autres
        Groupées par ouvrage (POSTE).
        """
        region_code = request.query_params.get('region')
        
        #Récupérer toutes les propositions ACCEPTEES ou EN_ATTENTE
        
        propositions = PropositionAlignement.objects.filter(
            statut__in=[
                 PropositionAlignement.Statut.EN_ATTENTE,
                PropositionAlignement.Statut.ACCEPTEE,
            ]
        ).select_related(
            'travail_a_modifier__reference__region',
            'travail_reference__reference__region',
            'travail_a_modifier__reference',
            'travail_reference__reference', 
        )
        
       # Filtrer par région si demandé
        if region_code:
            propositions = propositions.filter(
                travail_a_modifier__reference__region__code=region_code
            ) 
            
        # Initialiser les 3 catégories
        transport_transport = {}
        distribution_distribution = {}
        distribution_poste_source = {}
    

        for prop in propositions:
            t_ref = prop.travail_reference
            t_mod = prop.travail_a_modifier

            if not t_ref or not t_mod:
                continue

            # Récupérer le poste (ouvrage) commun
            poste_ref = _get_poste_from_travail(t_ref)
            region_ref = t_ref.reference.region.code if t_ref.reference and t_ref.reference.region else "Inconnue"

            # Construire la clé de regroupement
            cle = f"{poste_ref} ({region_ref})"

            prop_data = {
                "id": str(prop.id),
                "statut": prop.statut,
                "type_proposition": prop.type_proposition,
                "travail_reference": {
                    "id": str(t_ref.id),
                    "ressource": t_ref.reference.valeur if t_ref.reference else "",
                    "segment": t_ref.segment,
                    "type_alignement": t_ref.type_alignement,
                    "debut": t_ref.heure_debut_planifie.strftime('%d/%m/%Y %H:%M') if t_ref.heure_debut_planifie else None,
                    "fin": t_ref.heure_fin_planifie.strftime('%d/%m/%Y %H:%M') if t_ref.heure_fin_planifie else None,
                },
                "travail_a_modifier": {
                    "id": str(t_mod.id),
                    "ressource": t_mod.reference.valeur if t_mod.reference else "",
                    "segment": t_mod.segment,
                    "type_alignement": t_mod.type_alignement,
                    "ancien_debut": prop.ancien_debut.strftime('%d/%m/%Y %H:%M'),
                    "nouveau_debut": prop.nouveau_debut.strftime('%d/%m/%Y %H:%M'),
                },
            }
            
            # Catégorie 1 : TRANSPORT ↔ TRANSPORT
            if (t_ref.type_alignement == 'TRANSPORT' and
                    t_mod.type_alignement == 'TRANSPORT'):
                transport_transport.setdefault(cle, []).append(prop_data)

            # Catégorie 2 : DISTRIBUTION_LIGNE ↔ DISTRIBUTION_LIGNE
            elif (t_ref.type_alignement == 'DISTRIBUTION_LIGNE' and
                    t_mod.type_alignement in ['DISTRIBUTION_LIGNE', 'DISTRIBUTION_POSTE_SOURCE']):
                distribution_distribution.setdefault(cle, []).append(prop_data)

            # Catégorie 3 : DISTRIBUTION_POSTE_SOURCE comme référence
            elif t_ref.type_alignement == 'DISTRIBUTION_POSTE_SOURCE':
                distribution_poste_source.setdefault(cle, []).append(prop_data)

            # Catégorie 2 aussi : TRANSPORT → DISTRIBUTION (alignement standard)
            elif (t_ref.type_alignement == 'TRANSPORT' and
                    t_mod.type_alignement in ['DISTRIBUTION_LIGNE', 'DISTRIBUTION_POSTE_SOURCE']):
                distribution_distribution.setdefault(cle, []).append(prop_data)

        return Response({
            "alignements_transport_transport": {
                "total": sum(len(v) for v in transport_transport.values()),
                "par_ouvrage": [
                    {"ouvrage": k, "propositions": v}
                    for k, v in transport_transport.items()
                ]
            },
            "alignements_distribution_distribution": {
                "total": sum(len(v) for v in distribution_distribution.values()),
                "par_ouvrage": [
                    {"ouvrage": k, "propositions": v}
                    for k, v in distribution_distribution.items()
                ]
            },
            "alignements_distribution_poste_source": {
                "total": sum(len(v) for v in distribution_poste_source.values()),
                "par_ouvrage": [
                    {"ouvrage": k, "propositions": v}
                    for k, v in distribution_poste_source.items()
                ]
            },
        })
    



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
            "Utilisez le paramètre `entite_metier_id` pour filtrer les références "
            "appartenant à une entité métier spécifique (Production, Transport ou Distribution).\n\n"
            "**Exemple :** `GET /referentiel/references/?entite_metier_id=<uuid>`"
        ),
        parameters=[
            OpenApiParameter(
                name='entite_metier_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "UUID de l'entité métier. "
                    "Filtre les références associées à cette entité (ex: Production, Transport, Distribution)."
                ),
            ),
            OpenApiParameter(
                name='region_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="UUID de la région. Filtre les références associées à cette région.",
            ),
        ],
    ),
)


@extend_schema_view(**_REFERENCE_TAG)
class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = Reference.objects.select_related('entite_metier', 'region').prefetch_related('items__type').all().order_by('-date_creation')
    serializer_class = ReferenceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        entite_id = self.request.query_params.get('entite_metier_id')
        region_id = self.request.query_params.get('region_id')

        # Garde défensive : on ignore le paramètre s'il contient les valeurs
        # invalides "undefined" ou "null" (chaînes envoyées par JavaScript quand
        # la variable frontend n'est pas encore résolue).
        # Sans cette garde, Django lève une ValidationError en tentant de convertir
        # "undefined" en UUID → erreur 500 visible dans le navigateur.
        # Voir BUG-005 dans bug_all_planning.md
        VALEURS_INVALIDES = {'undefined', 'null', ''}
        if entite_id and entite_id not in VALEURS_INVALIDES:
            qs = qs.filter(entite_metier_id=entite_id)
        if region_id and region_id not in VALEURS_INVALIDES:
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
    queryset = ReferentielItem.objects.select_related('type', 'reference').all().order_by('-date_creation')
    serializer_class = ReferentielItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        reference_id = self.request.query_params.get('reference_id')
        type_id = self.request.query_params.get('type_id')
        # ReferentielItem n'a pas de champ entite_metier direct : il est lié
        # à une Reference, elle-même liée à une EntiteMetier. On remonte donc
        # cette chaîne (item -> reference -> entite_metier) pour filtrer.
        entite_metier_id = self.request.query_params.get('entite_metier_id')
        VALEURS_INVALIDES = {'undefined', 'null', ''}
        if reference_id:
            qs = qs.filter(reference_id=reference_id)
        if type_id:
            qs = qs.filter(type_id=type_id)
        if entite_metier_id and entite_metier_id not in VALEURS_INVALIDES:
            qs = qs.filter(reference__entite_metier_id=entite_metier_id)
        return qs


@extend_schema_view(**_TAG)
class TronconViewSet(viewsets.ModelViewSet):
    queryset = Troncon.objects.all().order_by('-date_creation')
    serializer_class = TronconSerializer

