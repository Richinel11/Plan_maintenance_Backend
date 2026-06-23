from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import(
    CentraleViewSet, TypeReferentielViewSet,
    ReferenceViewSet, ReferentielItemViewSet,
    RegionViewset
)

router = DefaultRouter()
router.register(r'centrales', CentraleViewSet, basename='centrale')
router.register(r'types', TypeReferentielViewSet, basename='type-referentiel')
router.register(r'references', ReferenceViewSet, basename='reference')
router.register(r'items', ReferentielItemViewSet, basename='referentiel-item')
router.register(r'regions', RegionViewset, basename='regions')

urlpatterns = [
    path('', include(router.urls)),
]
