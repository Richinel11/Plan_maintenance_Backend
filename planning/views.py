from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers as drf_serializers
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import Planning, Travail, TypeActivite, PropositionAlignement
from .serializers import PlanningSerializer, TravailSerializer, TypeActiviteSerializer, PropositionAlignementSerializer
from pilotage.models import Workflow, WorkflowStep
from .alignement_service import analyser_mois, _charge_disponible, _peut_bouger


@extend_schema_view(
    list=extend_schema(tags=["Planning"]),
    create=extend_schema(tags=["Planning"]),
    retrieve=extend_schema(tags=["Planning"]),
    update=extend_schema(tags=["Planning"]),
    partial_update=extend_schema(tags=["Planning"]),
    destroy=extend_schema(tags=["Planning"]),
)
class TypeActiviteViewSet(ModelViewSet):
    queryset = TypeActivite.objects.select_related('entite_metier').all().order_by('-date_creation')
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

    def get_queryset(self):
        qs = super().get_queryset()
        if (
            self.request.user.user_roles.filter(role__code_role='RESPONSABLE').exists()
            and not self.request.user.is_superuser
        ):
            qs = qs.filter(
                entite_metier=self.request.user.entite_metier,
                transmis_au_responsable=True,
            )
        return qs

    def perform_create(self, serializer):
        # Liaison automatique au workflow actif 
        # Il ne peut y avoir qu'un seul workflow actif à la fois.
        # On le récupère et on initialise le planning sur son premier step
        
        workflow_actif = Workflow.objects.filter(code='TRAVAUX_PROGRAMMES',is_active=True).first()

        first_step = None
        if workflow_actif:
            first_step = WorkflowStep.objects.filter(
                workflow=workflow_actif, code='EN_ATTENTE'
            ).first()
            if not first_step:
                first_step = WorkflowStep.objects.filter(workflow=workflow_actif).order_by('number').first()

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

    def destroy(self, request, *args, **kwargs):
        # Un planning ne peut être supprimé que tant qu'il est à son étape de
        # départ (EN_ATTENTE, le premier step du workflow actif). Dès qu'il
        # avance au-delà, la suppression est interdite : le planning est déjà
        # engagé dans le workflow.
        planning = self.get_object()
        step = planning.current_step
        if step and step.code != 'EN_ATTENTE':
            return Response(
                {"error": (
                    f"Suppression impossible : le planning est déjà à l'étape "
                    f"« {step.name} ». Seuls les plannings à l'étape « En attente » "
                    f"peuvent être supprimés."
                )},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

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

    @action(detail=True, methods=['POST'], url_path='transmettre-au-responsable')
    def transmettre_au_responsable(self, request, pk=None):
        """Finalise un import et alerte les responsables de la même entité."""
        planning = self.get_object()
        if planning.cree_par_id != request.user.id and not request.user.is_superuser:
            return Response(
                {"error": "Seul le créateur du planning peut finaliser sa transmission."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not planning.entite_metier_id:
            return Response(
                {"error": "L'entité métier est requise avant la transmission."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not planning.travaux.exists():
            return Response(
                {"error": "Un planning sans travaux ne peut pas être transmis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not planning.transmis_au_responsable:
            from exploitation.notification_service import alerter_responsables_planning_transmis

            planning.transmis_au_responsable = True
            planning.date_transmission = timezone.now()
            planning.modifie_par = request.user
            planning.save(update_fields=[
                'transmis_au_responsable', 'date_transmission', 'modifie_par',
                'date_modification',
            ])
            alerter_responsables_planning_transmis(planning)

        return Response(self.get_serializer(planning).data, status=status.HTTP_200_OK)
    
    # FONCTION POUR ALIGNER LES TRAVAUX SUR LE UN MOIS DONNEE

    @extend_schema(
        tags=["Planning - Alignement"],
        description=(
        "Analyse les chevauchements de TOUS les travaux sur une période mensuelle. "
        "Paramètres optionnels : ?annee=2026&mois=6 (par défaut : mois en cours). "
        "Option C : inclut tout travail dont la période chevauche le mois demandé."
        )
    )
    @action(detail=False, methods=['POST'], url_path='analyser-mois')
    def analyser_mois_complet(self, request):
        """Analyse les chevauchements de tous les travaux sur le mois courant
       (ou le mois/année passés en paramètres).
       Usage :
        POST /plannings/analyser-mois/
        Body optionnel : { "annee": 2026 (int), "mois": 7 (int) }
        Sans body -> mois en cours"""
        
        annee = request.data.get('annee') or request.query_params.get('annee')
        mois  = request.data.get('mois')  or request.query_params.get('mois')
        # Convertir en int si fournis
        try:
            annee = int(annee) if annee else None
            mois  = int(mois)  if mois  else None
        except (ValueError, TypeError):
            return Response(
                {"error": "annee et mois doivent être des entiers (ex: annee=2026, mois=7)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        #Validation des valeurs
        if mois and not (1 <= mois <=12):
            return Response(
                {"error": "mois doit etre entre 1 et 12"},
                status=status.HTTP_400_BAD_REQUEST
            )
        result = analyser_mois(
            user=request.user,
            annee=annee, # type: ignore
            mois=mois # type: ignore
            )

        propositions_data = PropositionAlignementSerializer(
            result['propositions'], many=True
        ).data

        return Response({
            "message":        result['message'],
            "periode":        result['periode'],
            "resume":         result['resume'],
            "chevauchements": result['chevauchements'],
            "propositions":   propositions_data
        }, status=status.HTTP_200_OK)
        
    @extend_schema(tags=["Planning - Aligenment"])
    @action(detail=True, methods=['GET'], url_path='propositions')
    
    def lister_propositions(self, request, pk=None):
        """Liste les propositions d'un planning avec filtre optionnel"""
        planning = self.get_object()
        statut_filtre = request.query_params.get('statut')
        pa = PropositionAlignement.objects.filter(planning=planning).select_related(
            'travail_a_modifier', 'travail_reference', 'cree_par'
        )
        if statut_filtre:
            pa = pa.filter(statut=statut_filtre)
        return Response((PropositionAlignementSerializer(pa, many=True).data), status=status.HTTP_200_OK)
        
    @extend_schema(tags=["Planning - Alignement"])
    @action(detail=True, methods=['POST'], url_path='appliquer-proposition')
    def appliquer_proposition(self, request, pk=None):
        """Accepter une proposition et appliquer les changements d'horaires"""
        planning = self.get_object()
        proposition_id = request.data.get('proposition_id')

        if not proposition_id:
            return Response({"error": "proposition_id est requis"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            proposition = PropositionAlignement.objects.select_related(
                'travail_a_modifier'
                ).get(id=proposition_id, planning=planning)
        except PropositionAlignement.DoesNotExist:
            return Response({
                "error-fr": "Proposition introuvable",
                "error-en": "Proposition not  found",
                },status=status.HTTP_404_NOT_FOUND)

        if proposition.statut == PropositionAlignement.Statut.BLOQUEE:
            return Response({
                "error-fr" : "Proposition bloquée impossible à appliquer",
                "error-en":  "Proposition blocked impossible to apply",
                "detail": proposition.detail_conflit or proposition.raison
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if proposition.statut != PropositionAlignement.Statut.EN_ATTENTE:
            return Response({
                "error-fr" : f"Proposition déjà '{proposition.statut}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        travail = proposition.travail_a_modifier

        # Revalidation à l'application : la disponibilité du chargé de
        # consignation a été calculée au moment de l'analyse (ou de la
        # dernière modification) et peut être périmée si, entre-temps, une
        # autre proposition partageant le même chargé a été appliquée sur un
        # créneau qui chevauche celui-ci. On ne fait plus confiance à
        # conflit_charge_consignation stocké : on revérifie à l'instant T.
        disponible, detail_conflit = _charge_disponible(
            travail.charge_consignation,
            proposition.nouveau_debut, proposition.nouvelle_fin,
            exclure_id=travail.id
        )
        if not disponible:
            proposition.statut = PropositionAlignement.Statut.BLOQUEE
            proposition.conflit_charge_consignation = True
            proposition.detail_conflit = detail_conflit
            proposition.save(update_fields=['statut', 'conflit_charge_consignation', 'detail_conflit', 'updated_at'])
            return Response({
                "error-fr": "Le chargé de consignation n'est plus disponible sur ce créneau (probablement suite à l'application d'une autre proposition entre-temps).",
                "error-en": "The consignment officer is no longer available for this slot.",
                "detail": detail_conflit,
                "proposition": PropositionAlignementSerializer(proposition).data,
            }, status=status.HTTP_409_CONFLICT)

        travail.heure_debut_planifie = proposition.nouveau_debut
        travail.heure_fin_planifie = proposition.nouvelle_fin
        travail.travail_en_alignement = True
        travail.modifie_par = request.user
        travail.save()
        
        proposition.statut = PropositionAlignement.Statut.ACCEPTEE
        proposition.save()
        
        return Response({
           "message": "Proposition acceptée. Horaires mis à jour.",
           "travail": {
            "id": str(travail.id),
            "ressource": travail.reference.valeur if travail.reference else str(travail.id),
            "nouveau_debut": travail.heure_debut_planifie,
            "nouvelle_fin": travail.heure_fin_planifie,
           },
           "proposition" : PropositionAlignementSerializer(proposition).data 
        }, status=status.HTTP_200_OK)
        
        
    # ─────────────────────────────────────────────────────────────────────────
    # ROUTE : GET /plannings/<id>/travaux/
    #
    # ROUTE : GET /plannings/<id>/travaux
    # Pourquoi cette route existe ici  et pas dans TravailViewSet?
    # TravailViewSet est une route independante(/travaux/)
    # Le frontend a besoin de recuperer les travaux d'un id precis via une URL
    # contextuelle : /plannings/<id>/travaux/
    # On ajoute donc une action imbriqué dans PlanningViewSet sans modifier les
    # routes presentes dans TravailViewset.
    
    # Ajouté pour corriger : BUG-004 (voir bug_all_planning.md)
    # ─────────────────────────────────────────────────────────────────────────
    @extend_schema(
        tags=["Planning"],
        responses={200: TravailSerializer(many=True)},
        description="Récupère tous les travaux appartenant à un planning donné"
    )
    @action(detail=True, methods=['GET'], url_path='travaux')
    def travaux_du_planning(self, request, pk=None):
        planning = self.get_object()

        # On filtre les travaux sur le planning courant.
        
        travaux = Travail.objects.filter(planning=planning).order_by('-date_creation').select_related(
            'type_travaux__entite_metier',   # couvre TypeActiviteSerializer.entite_metier
            'unite_demanderesse',
            'reference',
            'charge_consignation',
            'entite_metier',
        )
        
        serializer = TravailSerializer(travaux, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @extend_schema(tags=["Planning - Alignement"])
    @action(detail=True, methods=['POST'], url_path='refuser-proposition')
    def refuser_proposition(self, request, pk=None):
        """Refuse une proposition sans modifier le travail."""
        planning = self.get_object()
        proposition_id = request.data.get('proposition_id')
        if not proposition_id:
            return Response({"error": "proposition_id est requis"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            proposition = PropositionAlignement.objects.get(id=proposition_id, planning=planning)
        except PropositionAlignement.DoesNotExist:
            return Response({"error": "Proposition introuvable"}, status=status.HTTP_404_NOT_FOUND)

        if proposition.statut not in [
            PropositionAlignement.Statut.EN_ATTENTE,
            PropositionAlignement.Statut.BLOQUEE
        ]:
            return Response(
                {"error": f"Proposition déjà '{proposition.statut}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        proposition.statut = PropositionAlignement.Statut.REFUSEE
        proposition.save()

        return Response({
            "message": "Proposition refusée. Aucun changement appliqué.",
            "proposition": PropositionAlignementSerializer(proposition).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Planning - Alignement"],
        request=inline_serializer('ModifierPropositionSerializer', fields={
            'proposition_id': drf_serializers.UUIDField(),
            'nouveau_debut': drf_serializers.DateTimeField(),
            'nouvelle_fin': drf_serializers.DateTimeField(),
        }),
        description=(
            "Ajuste la date proposée avant application (le travail n'est pas "
            "encore modifié). Recalcule la disponibilité du chargé de "
            "consignation sur le nouveau créneau : la proposition peut passer "
            "de BLOQUEE à EN_ATTENTE ou inversement."
        ),
    )
    @action(detail=True, methods=['POST'], url_path='modifier-proposition')
    def modifier_proposition(self, request, pk=None):
        """Modifie les dates proposées d'une proposition en attente ou bloquée."""
        planning = self.get_object()
        proposition_id = request.data.get('proposition_id')
        nouveau_debut_raw = request.data.get('nouveau_debut')
        nouvelle_fin_raw = request.data.get('nouvelle_fin')

        if not proposition_id or not nouveau_debut_raw or not nouvelle_fin_raw:
            return Response({
                "error": "proposition_id, nouveau_debut et nouvelle_fin sont requis"
            }, status=status.HTTP_400_BAD_REQUEST)

        nouveau_debut = parse_datetime(nouveau_debut_raw)
        nouvelle_fin = parse_datetime(nouvelle_fin_raw)
        if not nouveau_debut or not nouvelle_fin:
            return Response({
                "error": "nouveau_debut/nouvelle_fin doivent être des dates ISO 8601 valides"
            }, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(nouveau_debut):
            nouveau_debut = timezone.make_aware(nouveau_debut)
        if timezone.is_naive(nouvelle_fin):
            nouvelle_fin = timezone.make_aware(nouvelle_fin)

        if nouveau_debut >= nouvelle_fin:
            return Response({
                "error": "nouveau_debut doit être antérieur à nouvelle_fin"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            proposition = PropositionAlignement.objects.select_related(
                'travail_a_modifier'
                ).get(id=proposition_id, planning=planning)
        except PropositionAlignement.DoesNotExist:
            return Response({"error": "Proposition introuvable"}, status=status.HTTP_404_NOT_FOUND)

        if proposition.statut not in [
            PropositionAlignement.Statut.EN_ATTENTE,
            PropositionAlignement.Statut.BLOQUEE
        ]:
            return Response(
                {"error": f"Proposition déjà '{proposition.statut}', non modifiable."},
                status=status.HTTP_400_BAD_REQUEST
            )

        travail = proposition.travail_a_modifier
        if not _peut_bouger(travail):
            return Response({
                "error-fr": "Ce travail (TRANSPORT ou P1) ne peut jamais être déplacé : la proposition n'est pas modifiable.",
                "error-en": "This work (TRANSPORT or P1) can never be moved: the proposal is not editable.",
            }, status=status.HTTP_400_BAD_REQUEST)

        disponible, detail_conflit = _charge_disponible(
            travail.charge_consignation,
            nouveau_debut, nouvelle_fin,
            exclure_id=travail.id
        )

        proposition.nouveau_debut = nouveau_debut
        proposition.nouvelle_fin = nouvelle_fin
        proposition.conflit_charge_consignation = not disponible
        proposition.detail_conflit = detail_conflit
        proposition.statut = (
            PropositionAlignement.Statut.BLOQUEE if not disponible
            else PropositionAlignement.Statut.EN_ATTENTE
        )
        proposition.raison = (
            f"[Modifiée manuellement par {request.user.get_full_name() or request.user.username}] "
            f"{proposition.raison}"
        )
        proposition.save()

        return Response({
            "message": "Proposition modifiée.",
            "proposition": PropositionAlignementSerializer(proposition).data
        }, status=status.HTTP_200_OK)
    

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
)
class TravailViewSet(ModelViewSet):
    # select_related doit couvrir toute la profondeur des relations imbriquées
    # sérialisées par TravailSerializer (via PlanningSerializer, ReferenceSerializer,
    # etc.) : sinon chaque relation manquante déclenche une requête par ligne
    # (N+1), ce qui a fini par provoquer un WORKER TIMEOUT sur /travaux/ quand
    # le nombre de travaux a augmenté.
    queryset = Travail.objects.all().order_by('-date_creation').select_related(
        'planning', 'planning__entite_metier', 'planning__workflow',
        'planning__current_step', 'planning__cree_par', 'planning__modifie_par',
        'type_travaux', 'type_travaux__entite_metier',
        'cree_par', 'modifie_par',
        'entite_metier', 'unite_demanderesse', 'unite_demanderesse__entite_metier',
        'reference', 'reference__entite_metier', 'reference__region',
        'charge_consignation', 'centrale_thermique_sollicitee',
        'demande_retrait', 'note_arret',
    ).prefetch_related('reference__items__type')
    serializer_class = TravailSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Dériver entite_metier automatiquement depuis le planning.
        # Le travail étant toujours rattaché à un planning qui lui-même
        # appartient à une entité métier, on évite la double saisie et
        # les incohérences potentielles entre les deux champs.
        # Si entite_metier est déjà fourni explicitement, on le respecte.
        extra = {
            'cree_par': self.request.user,
            'modifie_par': self.request.user,
        }
        planning = serializer.validated_data.get('planning')
        entite_explicite = serializer.validated_data.get('entite_metier')
        if planning and planning.entite_metier and not entite_explicite:
            extra['entite_metier'] = planning.entite_metier

        serializer.save(**extra)

    def perform_update(self, serializer):
        # Si le planning change lors d'une mise à jour et qu'aucune entité
        # n'est fournie explicitement, on synchronise entite_metier avec
        # celle du nouveau planning
        extra = {'modifie_par': self.request.user}
        planning = serializer.validated_data.get('planning')
        entite_explicite = serializer.validated_data.get('entite_metier')
        if planning and planning.entite_metier and not entite_explicite:
            extra['entite_metier'] = planning.entite_metier

        serializer.save(**extra)


    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
    
    # creation des travaux en fonction des Type(Distribution, Transport et Production)
    
    #  ACTIONS WORKFLOW 

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
                'BROUILLON', 'SOUMIS', 'VALIDE', 'REPORTE', 'EN_COURS', 'TERMINE', 'ANNULE'
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

    @staticmethod
    def _verifier_charge_consignation(request, travail):
        """
        Seul le chargé de consignation désigné sur le travail constate le réel
        (il est le seul présent sur le terrain). Renvoie une Response d'erreur,
        ou None si l'appelant est légitime.
        """
        if request.user.is_superuser:
            return None
        if travail.charge_consignation_id != request.user.id:
            return Response(
                {"error": "Seul le chargé de consignation désigné sur ce travail "
                          "peut effectuer cette action."},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    @action(detail=True, methods=['POST'])
    def demarrer(self, request, pk=None):
        """
        Démarrage du travail par le chargé de consignation (bouton ▶).

        L'heure de début réelle n'est pas saisie mais horodatée par le serveur
        au moment du clic : la donnée est mesurée et non déclarée, ce qui la
        rend exploitable par les KPI de suivi (cf. rapport_suivi_service).
        """
        travail = self.get_object()
        if travail.statut_travaux != 'VALIDE':
            return Response(
                {"error": "Le travail doit être VALIDE pour pouvoir démarrer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        napt = getattr(travail, 'note_arret', None)
        if napt is None or napt.statut != 'DIFFUSEE':
            return Response(
                {"error": "La NAPT du travail doit être diffusée pour pouvoir le démarrer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        erreur = self._verifier_charge_consignation(request, travail)
        if erreur:
            return erreur

        travail.statut_travaux = 'EN_COURS'
        travail.heure_debut_reel = timezone.now()
        travail.modifie_par = request.user
        travail.save()
        return Response({
            "status": "Travail en cours.",
            "heure_debut_reel": travail.heure_debut_reel,
        })

    @action(detail=True, methods=['POST'])
    def terminer(self, request, pk=None):
        """
        Clôture du travail par le chargé de consignation (bouton ⏹).

        Exige que le travail ait été démarré : un travail ne peut donc plus
        passer en TERMINE sans porter ses heures réelles.
        """
        travail = self.get_object()
        if travail.statut_travaux != 'EN_COURS':
            return Response(
                {"error": "Le travail doit avoir été démarré (EN_COURS) pour "
                          "pouvoir être terminé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        napt = getattr(travail, 'note_arret', None)
        if napt is None or napt.statut != 'DIFFUSEE':
            return Response(
                {"error": "La NAPT du travail doit être diffusée pour pouvoir le terminer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        erreur = self._verifier_charge_consignation(request, travail)
        if erreur:
            return erreur

        travail.statut_travaux = 'TERMINE'
        travail.heure_fin_reel = timezone.now()
        travail.modifie_par = request.user
        # duree_reelle_heures est déduite du couple début/fin dans Travail.save()
        travail.save()
        return Response({
            "status": "Travail terminé.",
            "heure_debut_reel": travail.heure_debut_reel,
            "heure_fin_reel": travail.heure_fin_reel,
            "duree_reelle_heures": travail.duree_reelle_heures,
        })

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

    @extend_schema(
        tags=["KPI - Travaux"],
        description=(
            "Retourne les travaux groupés par statut. "
            "Paramètres optionnels : "
            "?statut=BROUILLON (filtrer un statut précis), "
            "?planning_id=uuid (filtrer par planning), "
            "?segment=DISTRIBUTION (filtrer par segment)."
        )
    )
    @action(detail=False, methods=['GET'], url_path='par-statut')
    def travaux_par_statut(self, request):
        """
        Retourne les travaux groupés par statut avec compteurs.

        Statuts possibles :
        - BROUILLON  : créé, pas encore soumis
        - SOUMIS     : soumis pour validation
        - VALIDE     : validé par le responsable
        - EN_COURS   : travaux en cours d'exécution
        - TERMINE    : travaux terminés
        - REPORTE    : travaux reportés
        """
        # Filtres optionnels
        statut_filtre   = request.query_params.get('statut')
        planning_filtre = request.query_params.get('planning_id')
        segment_filtre  = request.query_params.get('segment')

        qs = self.get_queryset()

        if planning_filtre:
            qs = qs.filter(planning_id=planning_filtre)
        if segment_filtre:
            qs = qs.filter(segment=segment_filtre)

        # Si un statut précis est demandé, retourner juste ce statut
        if statut_filtre:
            statuts_valides = dict(Travail.STATUT_TRAVAUX)
            if statut_filtre not in statuts_valides:
                return Response(
                    {
                        "error": f"Statut invalide.",
                        "statuts_valides": list(statuts_valides.keys())
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            travaux = qs.filter(statut_travaux=statut_filtre)
            return Response({
                "statut": statut_filtre,
                "libelle": statuts_valides[statut_filtre],
                "total": travaux.count(),
                "travaux": self.get_serializer(travaux, many=True).data
            })

        # Sinon on retourne tous les statuts avec leurs travaux
        STATUTS = [
            ('BROUILLON', 'Brouillon'),
            ('SOUMIS',    'Soumis'),
            ('VALIDE',    'Validé'),
            ('EN_COURS',  'En cours'),
            ('TERMINE',   'Terminé'),
            ('REPORTE',   'Reporté'),
        ]

        resultat = []
        total_global = 0

        for code, libelle in STATUTS:
            travaux = qs.filter(statut_travaux=code)
            count = travaux.count()
            total_global += count
            resultat.append({
                "statut": code,
                "libelle": libelle,
                "total": count,
                "travaux": self.get_serializer(travaux, many=True).data
            })

        return Response({
            "total_global": total_global,
            "par_statut": resultat
        })

    def _filtrer_par_mois(self, qs, request):
        """Filtre un queryset de Travail sur date_programmee__year/month.
        Paramètres optionnels : ?annee=2026&mois=4"""
        annee = request.query_params.get('annee')
        mois  = request.query_params.get('mois')
        if annee:
            qs = qs.filter(date_programmee__year=annee)
        if mois:
            qs = qs.filter(date_programmee__month=mois)
        return qs

    @extend_schema(
        tags=["KPI - Travaux"],
        description=(
            "Retourne le nombre de travaux programmés (VALIDE), exécutés (TERMINE) "
            "et non exécutés (REPORTE). Paramètres optionnels : ?planning_id=uuid, "
            "?segment=DISTRIBUTION, ?annee=2026&mois=4 (filtre sur date_programmee)."
        )
    )
    @action(detail=False, methods=['GET'], url_path='kpi-resume')
    def kpi_resume(self, request):
        planning_filtre = request.query_params.get('planning_id')
        segment_filtre  = request.query_params.get('segment')

        qs = self.get_queryset()
        if planning_filtre:
            qs = qs.filter(planning_id=planning_filtre)
        if segment_filtre:
            qs = qs.filter(segment=segment_filtre)
        qs = self._filtrer_par_mois(qs, request)

        return Response({
            "programmes": qs.filter(statut_travaux='VALIDE').count(),
            "executes": qs.filter(statut_travaux='TERMINE').count(),
            "non_executes": qs.filter(statut_travaux='REPORTE').count(),
            "total": qs.count(),
        })

    @extend_schema(
        tags=["KPI - Travaux"],
        description=(
            "Retourne le nombre de travaux harmonisés (travaux distincts ayant au moins "
            "une proposition d'alignement ACCEPTEE). Paramètres optionnels : ?segment=DISTRIBUTION, "
            "?annee=2026&mois=4 (filtre sur date_programmee)."
        )
    )
    @action(detail=False, methods=['GET'], url_path='harmonises')
    def harmonises(self, request):
        segment_filtre = request.query_params.get('segment')

        travail_ids = PropositionAlignement.objects.filter(
            statut=PropositionAlignement.Statut.ACCEPTEE
        ).values_list('travail_a_modifier_id', flat=True).distinct()

        qs = self.get_queryset().filter(id__in=travail_ids)
        if segment_filtre:
            qs = qs.filter(segment=segment_filtre)
        qs = self._filtrer_par_mois(qs, request)

        return Response({
            "total_harmonises": qs.count(),
        })

    @extend_schema(
        tags=["KPI - Travaux"],
        description=(
            "Retourne le nombre de travaux programmés regroupés par ouvrage (poste pour "
            "Distribution/Transport, centrale sollicitée pour Production). Paramètres optionnels : "
            "?segment=DISTRIBUTION, ?annee=2026&mois=4 (filtre sur date_programmee). "
            "L'ouvrage est résolu à partir d'un champ texte libre : deux orthographes "
            "différentes du même ouvrage ne sont pas regroupées ensemble."
        )
    )
    @action(detail=False, methods=['GET'], url_path='par-ouvrage')
    def par_ouvrage(self, request):
        from collections import Counter
        from referentiel.kpi_service import _get_poste_from_travail

        segment_filtre = request.query_params.get('segment')
        qs = self.get_queryset()
        if segment_filtre:
            qs = qs.filter(segment=segment_filtre)
        qs = self._filtrer_par_mois(qs, request)

        compteur = Counter()
        for travail in qs:
            if travail.segment == 'PRODUCTION':
                ouvrage = travail.centrale_thermique_sollicitee.valeur if travail.centrale_thermique_sollicitee else "Inconnu"
            else:
                ouvrage = _get_poste_from_travail(travail)
            compteur[ouvrage] += 1

        resultat = [
            {"ouvrage": ouvrage, "total": total}
            for ouvrage, total in sorted(compteur.items(), key=lambda x: -x[1])
        ]

        return Response({
            "total_ouvrages": len(resultat),
            "par_ouvrage": resultat,
        })

    @extend_schema(
        tags=["KPI - Travaux"],
        description=(
            "Retourne le nombre de travaux Production regroupés selon que l'unité "
            "demanderesse est une IPP (nom contenant 'IPP') ou une entité interne ENEO. "
            "Heuristique basée sur le nom de l'unité demanderesse, faute de champ dédié "
            "de catégorisation dans le modèle actuel. Paramètre optionnel : ?annee=2026&mois=4."
        )
    )
    @action(detail=False, methods=['GET'], url_path='centrales-ipp-interne')
    def centrales_ipp_interne(self, request):
        qs = self.get_queryset().filter(segment='PRODUCTION')
        qs = self._filtrer_par_mois(qs, request)

        ipp = qs.filter(unite_demanderesse__nom__icontains='IPP').count()
        non_renseigne = qs.filter(unite_demanderesse__isnull=True).count()
        interne = qs.exclude(
            unite_demanderesse__nom__icontains='IPP'
        ).exclude(unite_demanderesse__isnull=True).count()

        return Response({
            "total": qs.count(),
            "ipp": ipp,
            "interne": interne,
            "non_renseigne": non_renseigne,
        })

    @extend_schema(
        tags=["KPI - Rapport suivi"],
        description=(
            "Rapport consolidé « Suivi des travaux prévisionnels » (tuiles de synthèse "
            "+ 5 tableaux : par région/mois, évolution mois M vs M-1 par segment, "
            "nombre de TP par segment/mois, durée des interruptions par segment, "
            "travaux exécutés en alignement). "
            "Paramètres optionnels : ?annee=2026&mois=5 (Mois M de référence pour les "
            "comparaisons M vs M-1 ; par défaut le mois courant). "
            "Les tableaux couvrent la période cumulée du 1er janvier de `annee` "
            "jusqu'à la fin de `mois` (year-to-date). "
            "Voir planning/rapport_suivi_service.py pour le détail des conventions "
            "de calcul (gain END alignée, taux de conformité, résolution de région)."
        )
    )
    @action(detail=False, methods=['GET'], url_path='rapport-suivi')
    def rapport_suivi(self, request):
        from .rapport_suivi_service import generer_rapport_suivi

        aujourdhui = timezone.localdate()
        try:
            annee = int(request.query_params.get('annee', aujourdhui.year))
            mois = int(request.query_params.get('mois', aujourdhui.month))
        except (TypeError, ValueError):
            return Response(
                {"error": "annee et mois doivent être des entiers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (1 <= mois <= 12):
            return Response(
                {"error": "mois doit être compris entre 1 et 12."},
                status=status.HTTP_400_BAD_REQUEST
            )

        rapport = generer_rapport_suivi(annee, mois, queryset=self.get_queryset())
        return Response(rapport)
