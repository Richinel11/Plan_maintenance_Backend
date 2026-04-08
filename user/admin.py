from django.contrib import admin
from .models import Utilisateur,EntiteMetier


# Register your models here.
@admin.register(Utilisateur)
class AdminUser(admin.ModelAdmin):
    list_display = ('id','username','nom','prenom','email','actif')
    list_filter = ('actif',)

@admin.register(EntiteMetier)
class AdminEntiteMetier(admin.ModelAdmin):
    list_display = ('id','nom','type',)
    list_filter = ('date_creation',)