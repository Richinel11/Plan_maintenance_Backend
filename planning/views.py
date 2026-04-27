# planning/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Q
from .models import PlanningTravaux, TypeActivite
from .serializers import PlanningTravauxSerializer, TypeActiviteSerializer

@extend_schema_view(
    list=extend_schema(tags=['TypeActivite'], description='Lister tous les types d\'activités'),
    retrieve=extend_schema(tags=['TypeActivite'], description='Récupérer un type d\'activité'),
    create=extend_schema(tags=['TypeActivite'], description='Créer un type d\'activité'),
    update=extend_schema(tags=['TypeActivite'], description='Mettre à jour un type d\'activité'),
    partial_update=extend_schema(tags=['TypeActivite'], description='Mettre à jour partiellement un type d\'activité'),
    destroy=extend_schema(tags=['TypeActivite'], description='Supprimer un type d\'activité'),
)
class TypeActiviteViewSet(ModelViewSet):
    """ViewSet CRUD pour TypeActivite."""

    queryset = TypeActivite.objects.all().order_by('libelle')
    serializer_class = TypeActiviteSerializer


@extend_schema_view(
    list=extend_schema(tags=['Planning'], description='Lister tous les travaux planifiés'),
    retrieve=extend_schema(tags=['Planning'], description='Détail d\'un travail planifié'),
    create=extend_schema(tags=['Planning'], description='Créer un travail planifié'),
    update=extend_schema(tags=['Planning'], description='Mettre à jour un travail planifié'),
    partial_update=extend_schema(tags=['Planning'], description='Mettre à jour partiellement un travail planifié'),
    destroy=extend_schema(tags=['Planning'], description='Supprimer un travail planifié'),
    reporter=extend_schema(tags=['Planning'], description='Reporter la date de fin et changer le statut en "REPORTE"'),
    changer_statut=extend_schema(tags=['Planning'], description='Changer le statut du travail'),
    soumettre=extend_schema(tags=['Planning'], description='Soumettre un travail pour validation'),
    valider=extend_schema(tags=['Planning'], description='Valider un travail soumis (Responsable)'),
    demarrer=extend_schema(tags=['Planning'], description='Démarrer un travail validé'),
    terminer=extend_schema(tags=['Planning'], description='Terminer un travail en cours'),
    conflits=extend_schema(tags=['Planning'], description='Lister les travaux en conflit'),
)

class PlanningTravauxViewSet(ModelViewSet):
    """ViewSet CRUD + actions custom pour PlanningTravaux."""

    queryset = PlanningTravaux.objects.all().order_by('-date_creation')
    serializer_class = PlanningTravauxSerializer

    # actions personnalisées pour le Workflow                                                            

    #Reporter la date de fin et passer le statut à REPORTE
    @action(detail=True, methods=['POST'])
    def reporter(self, request, pk=None):
        planning = self.get_object()
        nouvelle_date = request.data.get('date_report_travaux')
        if not nouvelle_date:
            return Response( {"error": "La nouvelle date est requise."},status=status.HTTP_400_BAD_REQUEST,)
        planning.date_report_travaux = nouvelle_date
        planning.statut_travaux = 'REPORTE'
        planning.save()
        return Response(self.get_serializer(planning).data)

    #Changer librement le statut du travail
    @action(detail=True, methods=['POST'])
    def changer_statut(self, request, pk=None):
        planning = self.get_object()
        nouveau_statut = request.data.get('statut_travaux')
        statuts_valides = dict(PlanningTravaux.STATUT_TRAVAUX)
        if nouveau_statut not in statuts_valides:
            return Response(
                {"error": f"Statut invalide. Valeurs acceptées : {list(statuts_valides.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,)
        planning.statut_travaux = nouveau_statut
        planning.save()
        return Response(self.get_serializer(planning).data)

    #Soumettre un travail en BROUILLON pour validation
    @action(detail=True, methods=['POST'])
    def soumettre(self, request, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'BROUILLON':
            return Response(
                {"error": "Le travail doit être en BROUILLON pour être soumis."},
                status=status.HTTP_400_BAD_REQUEST,)
        planning.statut_travaux = 'SOUMIS'
        planning.save()
        return Response({"status": "Travail soumis pour validation."})

    #Valider un travail SOUMIS (réservé au responsable d'exploitation)
    @action(detail=True, methods=['POST'])
    def valider(self, request, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'SOUMIS':
            return Response(
                {"error": "Le travail doit être SOUMIS pour être validé."},
                status=status.HTTP_400_BAD_REQUEST,)
            
        if request.user.role != 'responsable_exploitation':
            return Response(
                {"error": "Vous n'avez pas le droit de valider ce travail."},
                status=status.HTTP_403_FORBIDDEN,)
            
        planning.statut_travaux = 'VALIDE'
        planning.travail_en_alignement = False
        planning.save()
        return Response({"status": "Travail validé."})

    #Démarrer un travail VALIDE
    
    @action(detail=True, methods=['POST'])
    def demarrer(self, request, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'VALIDE':          
            return Response(
                {"error": "Le travail doit être VALIDE pour pouvoir démarrer."},
                status=status.HTTP_400_BAD_REQUEST,)
        planning.statut_travaux = 'EN_COURS'
        planning.jour_debut_effectif = request.data.get('jour_debut_effectif')
        planning.save()
        return Response({"status": "Travail en cours."})

    #Terminer un travail EN_COURS
    
    @action(detail=True, methods=['POST'])
    def terminer(self, request, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'EN_COURS':
            return Response(
                {"error": "Le travail doit être EN_COURS pour être terminé."},
                status=status.HTTP_400_BAD_REQUEST,)
        planning.statut_travaux = 'TERMINE'
        planning.save()
        return Response({"status": "Travail terminé."})

    # Gestion des Conflits                                                            

    #Retourne les IDs des travaux dont les périodes se chevauchent sur la même référence
    @action(detail=False, methods=['GET'])
    def conflits(self, request):
        travaux = self.get_queryset()
        ids_en_conflit = set()

        for t1 in travaux:
            en_conflit = travaux.filter(
                reference=t1.reference,
                jour_debut_planifie__lte=t1.jour_fin_planifie,
                jour_fin_planifie__gte=t1.jour_debut_planifie,).exclude(id=t1.id)

            if en_conflit.exists():
                ids_en_conflit.add(t1.id)

        return Response({"conflits": list(ids_en_conflit)})



























