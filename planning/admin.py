from django.contrib import admin
from .models import PlanningTravaux, TypeActivite

@admin.register(PlanningTravaux)
class AdminPlanningTraveaux(admin.ModelAdmin):
    list_display = ['reference', 'segment', 'type_travaux', 'statut_travaux', 'date_creation']
    list_filter = ['segment', 'type_travaux', 'statut_travaux']
    search_fields = ['reference']


@admin.register(TypeActivite)
class AdminTypeActivite(admin.ModelAdmin):
    list_display = ['libelle', 'date_creation']
