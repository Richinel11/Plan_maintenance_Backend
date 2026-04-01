
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UtilisateurViewSet, RoleViewSet, EntiteMetierViewSet

router = DefaultRouter()
router.register(r'users', UtilisateurViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'entites', EntiteMetierViewSet)

urlpatterns = [
    path('', include(router.urls)),
]