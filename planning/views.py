# planning/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers as drf_serializers
from .models import Planning, Travail, TypeActivite
from .serializers import PlanningSerializer, TravailSerializer, TypeActiviteSerializer
from pilotage.models import Workflow, WorkflowStep


@extend_schema_view(
    list=extend_schema(tags=["Planning"]),
    create=extend_schema(tags=["Planning"]),
    retrieve=extend_schema(tags=["Planning"]),
    update=extend_schema(tags=["Planning"]),
    partial_update=extend_schema(tags=["Planning"]),
    destroy=extend_schema(tags=["Planning"]),
)
class TypeActiviteViewSet(ModelViewSet):
    queryset = TypeActivite.objects.select_related('entite_metier').all().order_by('libelle')
    serializer_class = TypeActiviteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        entite_id = self.request.query_params.get('entite_metier_id')
        if entite_id:
            qs = qs.filter(entite_metier_id=entite_id)
        return qs


@extend_schema_view(
    list=extend_schema(tags=["Planning"]),
    create=extend_schema(tags=["Planning"]),
    retrieve=extend_schema(tags=["Planning"]),
    update=extend_schema(tags=["Planning"]),
    partial_update=extend_schema(tags=["Planning"]),
    destroy=extend_schema(tags=["Planning"]),
    assigner_workflow=extend_schema(tags=["Planning"]),
)
class PlanningViewSet(ModelViewSet):
    queryset = Planning.objects.all().order_by('-date_creation').select_related(
        'entite_metier', 'workflow', 'current_step', 'cree_par', 'modifie_par'
    )
    serializer_class = PlanningSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # ── Liaison automatique au workflow actif ──────────────────────────
        # Il ne peut y avoir qu'un seul workflow actif à la fois.
        # On le récupère et on initialise le planning sur son premier step.
        workflow_actif = Workflow.objects.filter(is_active=True).first()

        first_step = None
        if workflow_actif:
            first_step = WorkflowStep.objects.filter(
                workflow=workflow_actif
            ).order_by('number').first()

        serializer.save(
            cree_par=self.request.user,
            modifie_par=self.request.user,
            workflow=workflow_actif,
            current_step=first_step,
        )

    def perform_update(self, serializer):
        serializer.save(modifie_par=self.request.user)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=inline_serializer('AssignerWorkflowSerializer', fields={
            'workflow_id': drf_serializers.UUIDField()
        }),
        responses={200: PlanningSerializer, 400: {"type": "object"}, 404: {"type": "object"}},
        description="Assigner un workflow à un planning et initialiser automatiquement le step de départ"
    )
    @action(detail=True, methods=['POST'], url_path='assigner-workflow')
    def assigner_workflow(self, request, pk=None):
        planning = self.get_object()

        workflow_id = request.data.get('workflow_id')
        if not workflow_id:
            return Response(
                {"error": "workflow_id est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            return Response(
                {"error": "Workflow introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        initial_step = WorkflowStep.objects.filter(workflow=workflow).order_by('number').first()
        if not initial_step:
            return Response(
                {"error": "Ce workflow ne possède aucun step."},
                status=status.HTTP_400_BAD_REQUEST
            )

        planning.workflow = workflow
        planning.current_step = initial_step
        planning.modifie_par = request.user
        planning.save()

        serializer = self.get_serializer(planning)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=["Travail"]),
    create=extend_schema(tags=["Travail"]),
    retrieve=extend_schema(tags=["Travail"]),
    update=extend_schema(tags=["Travail"]),
    partial_update=extend_schema(tags=["Travail"]),
    destroy=extend_schema(tags=["Travail"]),
    reporter=extend_schema(tags=["Travail"]),
    changer_statut=extend_schema(tags=["Travail"]),
    soumettre=extend_schema(tags=["Travail"]),
    valider=extend_schema(tags=["Travail"]),
    demarrer=extend_schema(tags=["Travail"]),
    terminer=extend_schema(tags=["Travail"]),
    par_segment=extend_schema(tags=["Travail"]),
    conflits=extend_schema(tags=["Travail"]),
)
class TravailViewSet(ModelViewSet):
    queryset = Travail.objects.all().order_by('-date_creation').select_related(
        'planning', 'type_travaux', 'cree_par', 'modifie_par',
        'entite_metier', 'unite_demanderesse',
        'reference', 'charge_consignation', 'centrale_thermique_sollicitee',
    )
    serializer_class = TravailSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user, modifie_par=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modifie_par=self.request.user)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    # ── ACTIONS WORKFLOW ──

    @extend_schema(
        request=inline_serializer('ReporterSerializer', fields={
            'date_report_travaux': drf_serializers.DateField()
        }),
        responses={200: TravailSerializer, 400: {"type": "object"}},
        description="Reporter la date du travail et passer le statut à REPORTE"
    )
    @action(detail=True, methods=['POST'])
    def reporter(self, request, pk=None):
        travail = self.get_object()
        nouvelle_date = request.data.get('date_report_travaux')
        if not nouvelle_date:
            return Response(
                {"error": "La nouvelle date est requise."},
                status=status.HTTP_400_BAD_REQUEST
            )
        travail.date_report_travaux = nouvelle_date
        travail.statut_travaux = 'REPORTE'
        travail.save()
        return Response(self.get_serializer(travail).data)

    @extend_schema(
        request=inline_serializer('ChangerStatutSerializer', fields={
            'statut_travaux': drf_serializers.ChoiceField(choices=[
                'BROUILLON', 'SOUMIS', 'VALIDE', 'REPORTE', 'EN_COURS', 'TERMINE'
            ])
        }),
        responses={200: TravailSerializer, 400: {"type": "object"}},
        description="Changer librement le statut du travail"
    )
    @action(detail=True, methods=['POST'])
    def changer_statut(self, request, pk=None):
        travail = self.get_object()
        nouveau_statut = request.data.get('statut_travaux')
        statuts_valides = dict(Travail.STATUT_TRAVAUX)
        if nouveau_statut not in statuts_valides:
            return Response(
                {"error": f"Statut invalide. Valeurs acceptées : {list(statuts_valides.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        travail.statut_travaux = nouveau_statut
        travail.save()
        return Response(self.get_serializer(travail).data)

    @action(detail=True, methods=['POST'])
    def soumettre(self, request, pk=None):
        travail = self.get_object()
        if travail.statut_travaux != 'BROUILLON':
            return Response(
                {"error": "Le travail doit être en BROUILLON pour être soumis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        travail.statut_travaux = 'SOUMIS'
        travail.save()
        return Response({"status": "Travail soumis pour validation."})

    @action(detail=True, methods=['POST'])
    def valider(self, request, pk=None):
        travail = self.get_object()
        if travail.statut_travaux != 'SOUMIS':
            return Response(
                {"error": "Le travail doit être SOUMIS pour être validé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        travail.statut_travaux = 'VALIDE'
        travail.travail_en_alignement = False
        travail.save()
        return Response({"status": "Travail validé."})

    @action(detail=True, methods=['POST'])
    def demarrer(self, request, pk=None):
        travail = self.get_object()
        if travail.statut_travaux != 'VALIDE':
            return Response(
                {"error": "Le travail doit être VALIDE pour pouvoir démarrer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        travail.statut_travaux = 'EN_COURS'
        travail.save()
        return Response({"status": "Travail en cours."})

    @action(detail=True, methods=['POST'])
    def terminer(self, request, pk=None):
        travail = self.get_object()
        if travail.statut_travaux != 'EN_COURS':
            return Response(
                {"error": "Le travail doit être EN_COURS pour être terminé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        travail.statut_travaux = 'TERMINE'
        travail.save()
        return Response({"status": "Travail terminé."})

    # ── FILTRES ──

    @action(detail=False, methods=['GET'])
    def par_segment(self, request):
        segment = request.query_params.get('segment')
        if not segment:
            return Response(
                {"error": "Le paramètre segment est requis. Valeurs: DISTRIBUTION, TRANSPORT, PRODUCTION"},
                status=status.HTTP_400_BAD_REQUEST
            )
        travaux = self.get_queryset().filter(segment=segment)
        return Response(self.get_serializer(travaux, many=True).data)

    @action(detail=False, methods=['GET'])
    def conflits(self, request):
        """Retourne les travaux dont les périodes se chevauchent sur la même référence"""
        travaux = self.get_queryset().filter(
            heure_debut_planifie__isnull=False,
            heure_fin_planifie__isnull=False,
            reference__isnull=False,
        )
        ids_en_conflit = set()
        for t1 in travaux:
            en_conflit = travaux.filter(
                reference=t1.reference,
                heure_debut_planifie__lte=t1.heure_fin_planifie,
                heure_fin_planifie__gte=t1.heure_debut_planifie,
            ).exclude(id=t1.id)
            if en_conflit.exists():
                ids_en_conflit.add(str(t1.id))
        return Response({"conflits": list(ids_en_conflit)})
