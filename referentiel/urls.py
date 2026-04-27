from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'troncons', TronconViewSet, basename='troncon')
router.register(r'departs', DepartViewSet, basename='depart')
router.register(r'postes', PosteViewSet, basename='poste')
router.register(r'references', ReferenceReseauViewSet, basename='reference')
router.register(r'ouvrage', OuvrageViewset, basename='ouvrage')
router.register(r'Localisation', LocalisationViewset, basename='Localisation')

urlpatterns =[
     
    path('',   include((router.urls))),
]