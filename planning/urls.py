from rest_framework.routers import DefaultRouter
from .views import PlanningTravauxViewSet, TypeActiviteViewSet, ChargeConsignationViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'plannings', PlanningTravauxViewSet, basename='planningtravaux')
router.register(r'types-activite', TypeActiviteViewSet, basename='typeactivite')
router.register(r'charges-consignation', ChargeConsignationViewSet, basename='chargeconsignation')

urlpatterns = [
    path('', include(router.urls)),
]


# Les routes générées automatiquement par le router seront :
    
# Méthode   URL                                             Action

# GET       /plannings/                                     liste tous les plannings
# POST      /plannings/                                     créer un planning
# GET       /plannings/<id>/                                détail d'un planning
# PUT       /PATCH/plannings/<id>/                          modifier un planning
# DELETE    /plannings/<id>/                                supprimer un planning
# POST      /plannings/<id>/reporter/                       reporter un planning
# POST      /plannings/<id>/changer_statut/                 changer le statut
# POST      /plannings/<id>/soumettre/                      soumettre
# POST      /plannings/<id>/valider/                        valider
# POST      /plannings/<id>/demarrer/                       démarrer
# POST      /plannings/<id>/terminer/                       terminer
# GET       /plannings/conflits/                            voir les conflits
# GET       /plannings/par_segment/?segment=DISTRIBUTION    filtrer par segment
# GET       /types-activite/                                liste types activité
# POST      /types-activite/                                créer type activité
# GET       /charges-consignation/                          liste charges consignation
# POST      /charges-consignation/                          créer charge consignation

