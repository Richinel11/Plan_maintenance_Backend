from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Troncon, Depart, Localisation, ReferenceReseau, Poste, Ouvrage
from .serializers import *


class TronconViewSet(viewsets.ViewSet):

    def list(self, request):
        troncons = Troncon.objects.all().order_by('-date_creation')
        serializer = TronconSerializer(troncons, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        troncon = get_object_or_404(Troncon, id=pk)
        serializer = TronconSerializer(troncon)
        return Response(serializer.data)

    def create(self, request):
        serializer = TronconSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        troncon = get_object_or_404(Troncon, id=pk)
        serializer = TronconSerializer(troncon, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        troncon = get_object_or_404(Troncon, id=pk)
        troncon.delete()
        return Response(status=204)

    # Remplace ton "change_status"
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        troncon = get_object_or_404(Troncon, id=pk)
        troncon.actif = not troncon.actif
        troncon.save()
        return Response({
            "id": troncon.id,
            "actif": troncon.actif
        })
        
        
class DepartViewSet(viewsets.ViewSet):

    def list(self, request):
        departs = Depart.objects.all()
        serializer = DepartSerializer(departs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        depart = get_object_or_404(Depart, id=pk)
        depart.actif = not depart.actif
        depart.save()
        return Response({"actif": depart.actif})
    
    def retrieve(self, request, pk=None):
        depart = get_object_or_404(Depart, id=pk)
        serializer = DepartSerializer(depart)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = DepartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   #ouvrage viewset
    
class OuvrageViewset(viewsets.ViewSet):
    
    def list(self, request):
        ouvrage = Ouvrage.objects.all()
        serializer = OuvrageSerializer(ouvrage, many = True)
        return Response(serializer.data)
    
    
    def retrieve(self, request, pk=None):
        ouvrage = get_object_or_404(Ouvrage, id=pk)
        serializer = OuvrageSerializer(ouvrage)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = OuvrageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        ouvrage = get_object_or_404(Ouvrage, id=pk)
        serializer = OuvrageSerializer(ouvrage, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        ouvrage = get_object_or_404(Ouvrage, id=pk)
        ouvrage.delete()
        return Response(status=204)

    #localisation viewset
    
class LocalisationViewset(viewsets.ViewSet):
    def list(self, request):
        Loc = Localisation.objects.all()
        serializer = LocalisationSerializer(Loc,many = True)
        return Response(serializer.data)        
    
    def retrieve(self, request, pk=None):
        Loc = get_object_or_404(Localisation, id=pk)
        serializer = LocalisationSerializer(Loc)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = LocalisationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        Loc = get_object_or_404(Localisation, id=pk)
        serializer = LocalisationSerializer(Loc, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        Loc = get_object_or_404(Localisation, id=pk)
        Loc.delete()
        return Response(status=204)

    
    #poste Viewset
class PosteViewSet(viewsets.ViewSet):

    def list(self, request):
        postes = Poste.objects.all()
        serializer = PosteSerializer(postes, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        poste = get_object_or_404(Localisation, id=pk)
        serializer = PosteSerializer(poste)
        return Response(serializer.data)
    
    def create(self, request): 
        serializer = PosteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        poste = get_object_or_404(Poste, id=pk)
        poste.actif = not poste.actif
        poste.save()
        return Response({"actif": poste.actif})
   
   #reference reseau Viewset 
class ReferenceReseauViewSet(viewsets.ViewSet):

    def list(self, request):
        refs = ReferenceReseau.objects.all()
        serializer = ReferenceReseauSerializer(refs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        ref = get_object_or_404(ReferenceReseau, id=pk)
        serializer = ReferenceReseauSerializer(ref)
        return Response(serializer.data)
    
    def create(self, request): 
        serializer = ReferenceReseauSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'])
    def toggle_status(self, request, pk=None):
        ref = get_object_or_404(ReferenceReseau, id=pk)
        ref.actif = not ref.actif
        ref.save()
        return Response({"actif": ref.actif})