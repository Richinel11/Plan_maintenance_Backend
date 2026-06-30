from django.urls import path
from . import views

app_name = "pilotage"

urlpatterns = [

    # Workflow
    path('workflows/', views.workflow_list_create, name='workflow_list_create'),
    path('workflows/<uuid:workflow_id>/', views.workflow_detail, name='workflow_detail'),

    # Workflow Steps
    path('workflows/<uuid:workflow_id>/steps/', views.step_list_create, name='step_list_create'),
    path('workflows/<uuid:workflow_id>/steps/<uuid:step_id>/', views.step_detail, name='step_detail'),

    # Workflow Transitions
    path('workflows/<uuid:workflow_id>/transitions/', views.transition_list_create, name='transition_list_create'),
    path('workflows/<uuid:workflow_id>/transitions/<uuid:transition_id>/', views.transition_detail, name='transition_detail'),

    # Workflow Validations
    path('transitions/<uuid:transition_id>/validations/', views.validation_list_create, name='validation_list_create'),
    path('transitions/<uuid:transition_id>/validations/<uuid:validation_id>/', views.validation_detail, name='validation_detail'),

    # Exécution du workflow sur un planning
    path('planning/<uuid:planning_id>/transitions/', views.available_transitions, name='available_transitions'),
    path('planning/<uuid:planning_id>/transition/execute/', views.execute_workflow_transition, name='execute_transition'),
    path('planning/<uuid:planning_id>/transition/reject/', views.reject_workflow_transition, name='reject_transition'),
    path('planning/<uuid:planning_id>/history/', views.planning_workflow_history, name='workflow_history'),
    path('planning/<uuid:planning_id>/current-step/', views.planning_current_step, name='current_step'),
    
    # retourne les plannings d'un workflow spécifique
    path('workflows/<uuid:workflow_id>/plannings/', views.workflow_plannings, name='workflows_plannings')

]
