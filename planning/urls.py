from rest_framework.routers import DefaultRouter
from .views import PlanningTravauxViewSet, TypeActiviteViewSet
from .calendar_view import calendar_view

router = DefaultRouter()
router.register(r'plannings', PlanningTravauxViewSet, basename='planningtravaux')
router.register(r'types-activite', TypeActiviteViewSet, basename='typeactivite')
urlpatterns = router.urls