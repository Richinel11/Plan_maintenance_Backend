from django.contrib import admin
from .models import Planning, Travail, TypeActivite


@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'entite_metier', 'cree_par', 'date_creation']
    list_filter = ['entite_metier']
    search_fields = ['code', 'nom']


@admin.register(Travail)
class TravailAdmin(admin.ModelAdmin):
    list_display = ['reference', 'segment', 'planning', 'type_travaux', 'statut_travaux', 'date_creation']
    list_filter = ['segment', 'type_travaux', 'statut_travaux']
    search_fields = ['reference']


@admin.register(TypeActivite)
class TypeActiviteAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'date_creation']
