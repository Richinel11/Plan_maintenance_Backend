# planning/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from security.permission import HasPermission
from .models import PlanningTravaux, TypeActivite, ChargeConsignation
from .serializers import PlanningTravauxSerializer, TypeActiviteSerializer, ChargeConsignationSerializer

class TypeActiviteViewSet(ModelViewSet):
    """ViewSet CRUD pour TypeActivite."""

    queryset = TypeActivite.objects.all().order_by('libelle')
    serializer_class = TypeActiviteSerializer
    permission_classes = [IsAuthenticated]
    
class ChargeConsignationViewSet(ModelViewSet):
    """ViewSet CRUD pour ChargeConsignation."""
    
    queryset = ChargeConsignation.objects.all().order_by('-created_at')
    serializer_class = ChargeConsignationSerializer 
    permission_classes = [IsAuthenticated]   
    
class PlanningTravauxViewSet(ModelViewSet):
    """ViewSet CRUD + actions custom pour PlanningTravaux."""

    queryset = PlanningTravaux.objects.all().order_by('-date_creation').select_related(
        'type_travaux', 'cree_par', 'modifie_par', 'unite_demanderesse',
        'ouvrage', 'poste', 'depart', 'troncon',
        'charge_consignation', 'centrale_thermique_sollicitee',
        'workflow', 'current_step'
    )
    serializer_class = PlanningTravauxSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True  # force le partial sur tous les updates
        return super().update(request, *args, **kwargs)
    
    # ACTIONS WORKFLOW
    
    @action(detail=True, methods=['POST'])
    def reporter(self, request, pk=None):
        """Reporter la date et passer le statut à REPORTE"""
        planning = self.get_object()
        nouvelle_date = request.data.get('date_report_travaux')
        if not nouvelle_date:
            return Response(
                {"error": "La nouvelle date est requise."},
                status=status.HTTP_400_BAD_REQUEST
            )
        planning.date_report_travaux = nouvelle_date
        planning.statut_travaux = 'REPORTE'
        planning.save()
        return Response(self.get_serializer(planning).data)

    @action(detail=True, methods=['POST'])
    def changer_statut(self, request, pk=None):
        """Changer librement le statut du travail"""
        planning = self.get_object()
        nouveau_statut = request.data.get('statut_travaux')
        statuts_valides = dict(PlanningTravaux.STATUT_TRAVAUX)
        if nouveau_statut not in statuts_valides:
            return Response(
                {"error": f"Statut invalide. Valeurs acceptées : {list(statuts_valides.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        planning.statut_travaux = nouveau_statut
        planning.save()
        return Response(self.get_serializer(planning).data)

    @action(detail=True, methods=['POST'])
    def soumettre(self, request, pk=None):
        """Soumettre un travail en BROUILLON pour validation"""
        planning = self.get_object()
        if planning.statut_travaux != 'BROUILLON':
            return Response(
                {"error": "Le travail doit être en BROUILLON pour être soumis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        planning.statut_travaux = 'SOUMIS'
        planning.save()
        return Response({"status": "Travail soumis pour validation."})

    @action(detail=True, methods=['POST'])
    def valider(self, request, pk=None):
        """Valider un travail SOUMIS"""
        planning = self.get_object()
        if planning.statut_travaux != 'SOUMIS':
            return Response(
                {"error": "Le travail doit être SOUMIS pour être validé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        planning.statut_travaux = 'VALIDE'
        planning.travail_en_alignement = False
        planning.save()
        return Response({"status": "Travail validé."})

    @action(detail=True, methods=['POST'])
    def demarrer(self, request, pk=None):
        """Démarrer un travail VALIDE"""
        planning = self.get_object()
        if planning.statut_travaux != 'VALIDE':
            return Response(
                {"error": "Le travail doit être VALIDE pour pouvoir démarrer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        planning.statut_travaux = 'EN_COURS'
        planning.save()
        return Response({"status": "Travail en cours."})

    @action(detail=True, methods=['POST'])
    def terminer(self, request, pk=None):
        """Terminer un travail EN_COURS"""
        planning = self.get_object()
        if planning.statut_travaux != 'EN_COURS':
            return Response(
                {"error": "Le travail doit être EN_COURS pour être terminé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        planning.statut_travaux = 'TERMINE'
        planning.save()
        return Response({"status": "Travail terminé."})

    # FILTRES PAR SEGMENT

    @action(detail=False, methods=['GET'])
    def par_segment(self, request):
        """Filtrer les plannings par segment"""
        segment = request.query_params.get('segment')
        if not segment:
            return Response(
                {"error": "Le paramètre segment est requis. Valeurs: DISTRIBUTION, TRANSPORT, PRODUCTION"},
                status=status.HTTP_400_BAD_REQUEST
            )
        plannings = self.get_queryset().filter(segment=segment)
        serializer = self.get_serializer(plannings, many=True)
        return Response(serializer.data)
    
    # GESTION DES CONFLITS
    
    @action(detail=False, methods=['GET'])
    def conflits(self, request):
        """Retourne les plannings dont les périodes se chevauchent sur le même troncon"""
        travaux = self.get_queryset().filter(
            heure_debut_planifie__isnull=False,
            heure_fin_planifie__isnull=False
        )
        ids_en_conflit = set()

        for t1 in travaux:
            en_conflit = travaux.filter(
                troncon=t1.troncon,
                heure_debut_planifie__lte=t1.heure_fin_planifie,
                heure_fin_planifie__gte=t1.heure_debut_planifie,
            ).exclude(id=t1.id)

            if en_conflit.exists():
                ids_en_conflit.add(str(t1.id))

        return Response({"conflits": list(ids_en_conflit)})





