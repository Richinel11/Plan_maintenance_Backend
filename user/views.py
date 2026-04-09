from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view


from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404

from .models import Utilisateur, EntiteMetier
from security.models import Role
from .serializers import  SetPasswordSerializer, UtilisateurSerializer,  EntiteMetierSerializer

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenSerializer

class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer
    
    
@extend_schema_view(
    list=extend_schema(tags=['User'], description="Lister les utilisateurs"),
    retrieve=extend_schema(tags=['User'], description="Détail d’un utilisateur"),
    create=extend_schema(tags=['User'], description="Créer un utilisateur"),
    update=extend_schema(tags=['User'], description="Mettre à jour un utilisateur"),
    destroy=extend_schema(tags=['User'], description="Supprimer un utilisateur"),

    # actions custom

    toggle_status=extend_schema(tags=['User'], description="Activer / désactiver un utilisateur", responses={"200": {"actif": True}}),
    set_password=extend_schema(tags=['User'], request=SetPasswordSerializer, description="Changer le mot de passe"),
)

class UtilisateurViewSet(ModelViewSet):
    queryset = Utilisateur.objects.select_related("role", "entite_metier").all()
    serializer_class = UtilisateurSerializer
    
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



@extend_schema_view(
    list=extend_schema(tags=['User'], description="Lister les entités métier"),
    retrieve=extend_schema(tags=['User'], description="Détail d’une entité métier"),
    create=extend_schema(tags=['User'], description="Créer une entité métier"),
    update=extend_schema(tags=['User'], description="Mettre à jour une entité métier"),
    destroy=extend_schema(tags=['User'], description="Supprimer une entité métier"),
)

class EntiteMetierViewSet(ModelViewSet):
    queryset = EntiteMetier.objects.all()
    serializer_class = EntiteMetierSerializer