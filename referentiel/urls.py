from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CentraleViewSet, TypeReferentielViewSet, ReferenceViewSet, ReferentielItemViewSet, RegionViewSet

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'centrales', CentraleViewSet, basename='centrale')
router.register(r'types', TypeReferentielViewSet, basename='type-referentiel')
router.register(r'references', ReferenceViewSet, basename='reference')
router.register(r'items', ReferentielItemViewSet, basename='referentiel-item')

urlpatterns = [
    path('', include(router.urls)),
]
