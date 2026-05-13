from rest_framework.routers import DefaultRouter
from .views import PlanningViewSet, TravailViewSet, TypeActiviteViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'plannings', PlanningViewSet, basename='planning')
router.register(r'travaux', TravailViewSet, basename='travail')
router.register(r'types-activite', TypeActiviteViewSet, basename='typeactivite')

urlpatterns = [
    path('', include(router.urls)),
]

# Routes générées :
#
# GET/POST    /plannings/                             liste / créer un planning
# GET/PATCH   /plannings/<id>/                        détail / modifier un planning
# DELETE      /plannings/<id>/                        supprimer un planning
#
# GET/POST    /travaux/                               liste / créer un travail
# GET/PATCH   /travaux/<id>/                          détail / modifier un travail
# DELETE      /travaux/<id>/                          supprimer un travail
# POST        /travaux/<id>/reporter/                 reporter
# POST        /travaux/<id>/changer_statut/           changer le statut
# POST        /travaux/<id>/soumettre/                soumettre
# POST        /travaux/<id>/valider/                  valider
# POST        /travaux/<id>/demarrer/                 démarrer
# POST        /travaux/<id>/terminer/                 terminer
# GET         /travaux/conflits/                      voir les conflits
# GET         /travaux/par_segment/?segment=XXX       filtrer par segment
#
# GET/POST    /types-activite/                        types d'activité
