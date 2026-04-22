from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur,EntiteMetier


# Register your models here.
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('id','username','first_name','last_name','email','is_active')
    list_filter = ('is_active',)

@admin.register(EntiteMetier)
class AdminEntiteMetier(admin.ModelAdmin):
    list_display = ('id','name','type',)
    list_filter = ('created_at',)