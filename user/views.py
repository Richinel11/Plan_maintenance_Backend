from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404

from .models import Utilisateur, EntiteMetier
from security.models import Role
from .serializers import UtilisateurSerializer,  EntiteMetierSerializer


class UtilisateurViewSet(ModelViewSet):
    queryset = Utilisateur.objects.select_related("role", "entite_metier").all()
    serializer_class = UtilisateurSerializer
    
    #login api
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Champs requis"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Utilisateur.objects.get(username=username, actif=True)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur non trouvé"}, status=404)

        if not check_password(password, user.password):
            return Response({"error": "Mot de passe incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Connexion réussie",
            "user": UtilisateurSerializer(user).data
        })
        
 
    
    # changer de statut
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        user = self.get_object()

        user.actif = not user.actif
        user.save()

        return Response({
            "id": str(user.id),
            "actif": user.actif
        })
        

        
      # changer de password
    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        user = self.get_object()

        password = request.data.get("password")

        if not password:
            return Response({"error": "Mot de passe requis"}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(password)
        user.first_connection = False
        user.save()

        return Response({"message": "Mot de passe mis à jour"})




class EntiteMetierViewSet(ModelViewSet):
    queryset = EntiteMetier.objects.all()
    serializer_class = EntiteMetierSerializer