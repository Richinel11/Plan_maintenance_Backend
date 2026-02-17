from django.contrib import admin
from .models import Troncon, Ouvrage, ReferenceReseau, Depart, Poste, Localisation
# Register your models here.

@admin.register(Troncon)
class AdminTroncons(admin.ModelAdmin):
    list_display = ('id','nom','date_creation')
 

@admin.register(Ouvrage)
class AdminOuvrage(admin.ModelAdmin):
    list_display = ('id','nom','type','date_creation')


@admin.register(Depart)
class AdminDepart(admin.ModelAdmin):
    list_display = ('id','nom','date_creation')


@admin.register(Poste)
class AdminPoste(admin.ModelAdmin):
    list_display = ('id','nom','date_creation')


@admin.register(Localisation)
class AdminLocalisation(admin.ModelAdmin):
    list_display = ('id','adresse','ville','longitude','latitude','date_creation')


@admin.register(ReferenceReseau)
class AdminReferenceReseau(admin.ModelAdmin):
    list_display = ('id','code_reference','libelle','ouvrage','poste','depart','troncon','localisation',)
    list_filter =('date_creation',)

