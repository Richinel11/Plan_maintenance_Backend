from django.contrib import admin
from .models import Centrale, TypeReferentiel, Reference, ReferentielItem, Region


@admin.register(Centrale)
class AdminCentrale(admin.ModelAdmin):
    list_display = ('id', 'valeur')


@admin.register(TypeReferentiel)
class AdminTypeReferentiel(admin.ModelAdmin):
    list_display = ('id', 'nom')


@admin.register(Reference)
class AdminReference(admin.ModelAdmin):
    list_display = ('id', 'valeur')


@admin.register(ReferentielItem)
class AdminReferentielItem(admin.ModelAdmin):
    list_display = ('id', 'valeur', 'type', 'reference')
    list_filter = ('type',)

@admin.register(Region)
class AdminRegion(admin.ModelAdmin):
    list_display = ('id', 'code')