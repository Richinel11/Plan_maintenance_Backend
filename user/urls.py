
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UtilisateurViewSet, EntiteMetierViewSet
router = DefaultRouter()
router.register(r'users', UtilisateurViewSet)
router.register(r'entites', EntiteMetierViewSet)

urlpatterns = [
    path('', include(router.urls)),
]