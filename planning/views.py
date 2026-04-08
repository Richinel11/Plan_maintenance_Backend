#plnaning/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import PlanningTravaux, TypeActivite
from .serializers import PlanningTravauxSerializer, TypeActiviteSerializer




class TypeActiviteViewSet(viewsets.ViewSet):

    #ViewSet pour CRUD TypeActivite
    

    def list(self, request):
        
        #Liste tous les types d'activités
        
        types = TypeActivite.objects.all().order_by('libelle')
        serializer = TypeActiviteSerializer(types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        
        #Récupère un type d'activité spécifique
        
        type_activite = get_object_or_404(TypeActivite, id=pk)
        serializer = TypeActiviteSerializer(type_activite)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        
        #Crée un nouveau type d'activité
        
        serializer = TypeActiviteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        
        #Mettre à jour un type d'activité existant
        
        type_activite = get_object_or_404(TypeActivite, id=pk)
        serializer = TypeActiviteSerializer(type_activite, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        
        #Supprime un type d'activité
        
        type_activite = get_object_or_404(TypeActivite, id=pk)
        type_activite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PlanningTravauxViewSet(viewsets.ViewSet):
    
    #ViewSet CRUD + actions custom pour PlanningTravaux
    

    def list(self, request):
        plannings = PlanningTravaux.objects.all().order_by('-date_creation')
        serializer = PlanningTravauxSerializer(plannings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        planning = get_object_or_404(PlanningTravaux, id=pk)
        serializer = PlanningTravauxSerializer(planning)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = PlanningTravauxSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        planning = get_object_or_404(PlanningTravaux, id=pk)
        serializer = PlanningTravauxSerializer(planning, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        planning = get_object_or_404(PlanningTravaux, id=pk)
        planning.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    #  fonctions de customisation

    @action(detail=True, methods=['POST'])
    def reporter(self, request, pk=None):
        
        #Reporter la date de fin et changer le statut en 'REPORTE'
        
        planning = get_object_or_404(PlanningTravaux, id=pk)
        nouvelle_date = request.data.get('date_report_travaux')
        if not nouvelle_date:
            return Response({"error": "La nouvelle date est requise"}, status=status.HTTP_400_BAD_REQUEST)
    
        planning.date_report_travaux = nouvelle_date
        planning.statut_travaux = 'REPORTE'
        planning.save()
        serializer = PlanningTravauxSerializer(planning)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def changer_statut(self, request, pk=None):
        
        #Permet de changer le statut des travaux (BROUILLON, SOUMIS, VALIDE, EN_COURS, TERMINE)
        
        planning = get_object_or_404(PlanningTravaux, id=pk)
        nouveau_statut = request.data.get('statut_travaux')
        if nouveau_statut not in dict(PlanningTravaux.STATUT_TRAVAUX):
            return Response({"error": "Statut invalide"}, status=status.HTTP_400_BAD_REQUEST)

        planning.statut_travaux = nouveau_statut
        planning.save()
        serializer = PlanningTravauxSerializer(planning)
        return Response(serializer.data, status=status.HTTP_200_OK)



 # fonctions personnalisées pour la gestion du workflow

    @action(detail=True, methods=['POST'])
    def soumettre(self, requests, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'BROUILLON':
            return Response({"error": "Le travail doit être en brouillon pour être soumis."}, status=status.HTTP_400_BAD_REQUEST)
        planning.statut_travaux = 'SOUMIS'
        planning.save()
        return Response({"status": "Travail soumis pour validation."})

    @action(detail=True, methods=['POST'])
    def valider(self, request, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'SOUMIS':
            return Response({"error": "Le travail doit être soumis pour être validé."}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.role != 'responsable_exploitation':
            return Response({"error": "Vous n'avez pas le droit de valider ce travail"}, status=status.HTTP_403_FORBIDDEN)
        planning.statut_travaux = 'VALIDE'
        planning.travail_en_alignement = False
        planning.save()
        return Response({"status": "Travail validé."})

    @action(detail=True, methods=['POST'])
    def demarrer(self, request, pk=None):
        planning= self.get_object()
        if planning.status_travaux != 'VALIDE':
            return Response({"error": "le travail doit être validé pour pouvoir démarrer."}, status=status.HTTP_400_BAD_REQUEST)
        planning.statut_travaux = 'EN_COURS'
        planning.jour_debut_effectif=request.data.get('jour_debut_effectif') 
        planning.save()
        return Response({"status": "travail en cours"})

    @action(detail=True, methods=['POST'])
    def terminer(self, request, pk=None):
        planning = self.get_object()
        if planning.statut_travaux != 'EN_COURS':
            return Response({"error": "Le travail doit être en cours pour être terminé."}, status=status.HTTP_400_BAD_REQUEST)
        planning.statut_travaux = 'TERMINE'
        planning.save()
        return Response({"status": "Travail terminé."})
    
    # Gestion des conflits
    
    @action(detail=False, methods=['GET'])
    def conflits(self, request):
        travaux = PlanningTravaux.objects.all()
        conflits = []

        for t1 in travaux:
            for t2 in travaux:
                if t1.id != t2.id and t1.reference == t2.reference:
                    if t1.jour_debut_planifie <= t2.jour_fin_planifie:
                        conflits.append(t1.id)

        return Response({"conflits": conflits})

   