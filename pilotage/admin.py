from django.contrib import admin
from .models import *

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'number', 'name', 'is_terminal')
    list_filter = ('workflow',)
    ordering = ('workflow', 'number')


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow', 'from_step', 'to_step', 'is_active')
    list_filter = ('workflow', 'is_active')


@admin.register(WorkflowValidation)
class WorkflowValidationAdmin(admin.ModelAdmin):
    list_display = ('transition', 'role', 'status', 'created_at')
    list_filter = ('status', 'role')


@admin.register(WorkflowHistory)
class WorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = ('planning', 'from_step', 'to_step', 'performed_by', 'transitioned_at')
    list_filter = ('transitioned_at',)