from rest_framework.routers import DefaultRouter
from .views import PlanningTravauxViewSet, TypeActiviteViewSet


router = DefaultRouter()
router.register(r'plannings', PlanningTravauxViewSet, basename='planningtravaux')
router.register(r'types-activite', TypeActiviteViewSet, basename='typeactivite')
urlpatterns = router.urls

