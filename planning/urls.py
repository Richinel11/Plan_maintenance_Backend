from rest_framework.routers import DefaultRouter
from .views import (
    PlanningViewSet, TravailViewSet,
    TypeActiviteViewSet,
)
from django.urls import path, include
from user.views import get_charges_consignation

router = DefaultRouter()

# Planning
router.register(r'plannings', PlanningViewSet, basename='planning')

# Types d'activités
router.register(r'types-activite', TypeActiviteViewSet, basename='typeactivite')

#Travaux génériques (pour lire tous les travaux)
router.register(r'travaux', TravailViewSet, basename='travail')

urlpatterns = [
    path('charges-consignation/', get_charges_consignation, name='charges-consignation'),
    path('', include(router.urls)),
]


# Routes générées :
#POST         /plannings/analyser-mois/ + body {"annee": 2026, "mois": 7} Juillet 2026
#POST         /plannings/analyser-mois/ + body {"mois": 7}           Juillet mois en cours
#POST         /plannings/analyser-mois/                            Mois en cours

# POST        /plannings/{id}/analyser-chevauchements/   
# GET         /plannings/{id}/propositions/?statut=EN_ATTENTE
# POST        /plannings/{id}/appliquer-proposition/      appliquer les propositions
# POST        /plannings/{id}/refuser-proposition/        refuser les propositions
#
# GET/POST    /plannings/                             liste / créer un planning
# GET/PATCH   /plannings/<id>/                        détail / modifier un planning
# DELETE      /plannings/<id>/                        supprimer un planning
# POST        /plannings/<id>/assigner-workflow/      assigner un workflow et initialiser le step de départ
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


# GET  travaux/par-statut/                      Tous les statuts 
# GET  travaux/par-statut/?statut=BROUILLON     Seulement les brouillons 
# GET  travaux/par-statut/?segment=TRANSPORT    Travaux Transport par statut 
# GET  travaux/par-statut/?planning_id=uuid     Travaux d'un planning par statut