from django.contrib import admin
from .models import PlanningTravaux, TypeActivite, ChargeConsignation

@admin.register(PlanningTravaux)
class AdminPlanningTraveaux(admin.ModelAdmin):
    list_display = ['reference', 'segment', 'type_travaux', 'statut_travaux', 'date_creation']
    list_filter = ['segment', 'type_travaux', 'statut_travaux']
    search_fields = ['reference']


@admin.register(TypeActivite)
class AdminTypeActivite(admin.ModelAdmin):
    list_display = ['libelle', 'date_creation']


@admin.register(ChargeConsignation)
class AdminChargeConsignation(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'matricule']