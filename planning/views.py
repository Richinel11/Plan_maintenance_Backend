# planing/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import PlanningTravaux, TypeActivite
from .serializers import PlanningTravauxSerializer, TypeActiviteSerializer

class TypeActiviteViewSet(viewsets.ViewSet):
    """
    ViewSet pour CRUD TypeActivite
    """

    def list(self, request):
        
        "Lister toutes les types d'activités"
        
        types = TypeActivite.objects.all().order_by('libelle')
        serializer = TypeActiviteSerializer(types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        
        "Récupèrer un type d'activité spécifique"
        
        type_activite = get_object_or_404(TypeActivite, id=pk)
        serializer = TypeActiviteSerializer(type_activite)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        
        "Crée un nouveau type d'activité"
        
        serializer = TypeActiviteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        
        "Met à jour un type d'activité existant"
        
        type_activite = get_object_or_404(TypeActivite, id=pk)
        serializer = TypeActiviteSerializer(type_activite, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        
        "Supprime un type d'activité"
        
        type_activite = get_object_or_404(TypeActivite, id=pk)
        type_activite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PlanningTravauxViewSet(viewsets.ViewSet):
    
    "ViewSet pour CRUD PlanningTravaux"
    
    
    def list(self, request):
        
        "Lister tous les plannings"
        
        plannings = PlanningTravaux.objects.all().order_by('-date_creation')
        serializer = PlanningTravauxSerializer(plannings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
    
        "Récupèrer un planning spécifique"
    
        planning = get_object_or_404(PlanningTravaux, id=pk)
        serializer = PlanningTravauxSerializer(planning)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        
        "Créer un nouveau planning"
        
        serializer = PlanningTravauxSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        
        "Mettre à jour un planning existant"
        
        planning=get_object_or_404(PlanningTravaux, id=pk)
        serializer = PlanningTravauxSerializer(planning, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        
        "Supprimer un planning"
    
        planning = get_object_or_404(PlanningTravaux, id=pk)
        planning.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def reporter(self, request, pk=None):
        
        "Permet de reporter la date d'un planning"
        
        planning = get_object_or_404(PlanningTravaux, id=pk)
        nouvelle_date = request.data.get('date_report_travaux')
        if not nouvelle_date:
            return Response({"error": "La nouvelle date est requise"}, status=status.HTTP_400_BAD_REQUEST)
        
        planning.date_report_travaux = nouvelle_date
        planning.statut_travaux = 'REPORTE'
        planning.save()
        serializer = PlanningTravauxSerializer(planning)
        return Response(serializer.data, status=status.HTTP_200_OK)
    