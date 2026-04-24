from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRole
# Register your models here.


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("nom", "code_role", "date_creation")
    list_filter = ("date_creation",)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "module")
    search_fields = ("nom", "code", "module")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role")

