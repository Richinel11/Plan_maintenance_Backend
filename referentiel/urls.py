from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import(
    CentraleViewSet, TypeReferentielViewSet,
    ReferenceViewSet, ReferentielItemViewSet,
    RegionViewset, TronconViewSet
)

router = DefaultRouter()
router.register(r'centrales', CentraleViewSet, basename='centrale')
router.register(r'types', TypeReferentielViewSet, basename='type-referentiel')
router.register(r'references', ReferenceViewSet, basename='reference')
router.register(r'items', ReferentielItemViewSet, basename='referentiel-item')
router.register(r'regions', RegionViewset, basename='regions')
router.register(r'troncons', TronconViewSet, basename='troncon')

urlpatterns = [
    path('', include(router.urls)),
]


#================================
# ROUTES POUR LES KPI
#================================

# GET regions/plannings/               Plannings par région
# GET regions/plannings/?region=DRY    Plannings de la région DRY
# GET regions/alignements/             Alignements par type et ouvrage
# GET regions/alignements/?region=DRD  Alignements de la région DRD