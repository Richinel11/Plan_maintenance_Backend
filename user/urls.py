
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UtilisateurViewSet, EntiteMetierViewSet, CustomTokenView
router = DefaultRouter()
router.register(r'users', UtilisateurViewSet)
router.register(r'entites', EntiteMetierViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', CustomTokenView.as_view(), name="token_obtain_pair"),
]



