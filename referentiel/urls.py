from rest_framework.routers import DefaultRouter
from .views import TronconViewSet, DepartViewSet, PosteViewSet, ReferenceReseauViewSet

router = DefaultRouter()
router.register(r'troncons', TronconViewSet, basename='troncon')
router.register(r'departs', DepartViewSet, basename='depart')
router.register(r'postes', PosteViewSet, basename='poste')
router.register(r'references', ReferenceReseauViewSet, basename='reference')

urlpatterns = router.urls