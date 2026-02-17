from django.contrib import admin
from .models import PlanningTravaux, TypeActivite

# Register your models here.
@admin.register(PlanningTravaux)
class AdminPlanningTraveaux(admin.ModelAdmin):
    list_display = ('id','titre','reference','type_activite','titre','statut_travaux','date_creation',)
    list_filter  = ('date_creation','type_activite')



@admin.register(TypeActivite)
class AdminTypeActivite(admin.ModelAdmin):
    list_display = ('id','libelle','date_creation')