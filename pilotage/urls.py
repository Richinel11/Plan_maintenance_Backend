from django.urls import path
from . import views
app_name = "pilotage"
   
urlpatterns = [

    # crud Workflow 
    path('workflows/all-workflows', views.workflow_list_create, name='workflow_list'),
    path('workflows/create-workflow', views.workflow_list_create, name='workflow_create'),
    path('workflows/find-workflow/<uuid:workflow_id>', views.workflow_detail, name='workflow_detail'),
    path('workflows/update-workflow/<uuid:workflow_id>', views.workflow_detail, name='workflow_update'),
    path('workflows/delete-workflow/<uuid:workflow_id>', views.workflow_detail, name='workflow_delete'),

    # crud workflow-Steps 
    path('workflows/<uuid:workflow_id>/all-steps', views.step_list_create, name='step_list'),
    path('workflows/<uuid:workflow_id>/create-step', views.step_list_create, name='step_create'),
    path('workflows/<uuid:workflow_id>/find-step/<uuid:step_id>', views.step_detail, name='step_detail'),
    path('workflows/<uuid:workflow_id>/update-step/<uuid:step_id>', views.step_detail, name='step_update'),
    path('workflows/<uuid:workflow_id>/delete-step/<uuid:step_id>', views.step_detail, name='step_delete'),


    # crud Workflow Transitions 
    path('workflows/<uuid:workflow_id>/all-transitions', views.transition_list_create, name='transition_list'),
    path('workflows/<uuid:workflow_id>/create-transition', views.transition_list_create, name='transition_create'),

    path('workflows/<uuid:workflow_id>/find-transition/<uuid:transition_id>', views.transition_detail, name='transition_detail'),
    path('workflows/<uuid:workflow_id>/update-transition/<uuid:transition_id>', views.transition_detail, name='transition_update'),
    path('workflows/<uuid:workflow_id>/delete-transition/<uuid:transition_id>', views.transition_detail, name='transition_delete'),

    # crud Workflow Validations 
    path('transitions/<uuid:transition_id>/all-validations', views.validation_list_create, name='validation_list'),
    path('transitions/<uuid:transition_id>/create-validation', views.validation_list_create, name='validation_create'),

    path('transitions/<uuid:transition_id>/validation/<uuid:validation_id>', views.validation_detail, name='validation_detail'),
    path('transitions/<uuid:transition_id>/validation/<uuid:validation_id>', views.validation_detail, name='validation_update'),
    path('transitions/<uuid:transition_id>/validation/<uuid:validation_id>', views.validation_detail, name='validation_delete'),

    #  ROUTES POUR L'EXECUTION DU WORKFLOW
    
    # Transitions disponibles pour un planning
    path('planning/<uuid:planning_id>/transitions', views.available_transitions, name='available_transitions'),
    # Exécuter une transition
    path('planning/<uuid:planning_id>/transition/execute', views.execute_workflow_transition, name='execute_transition'),
    # Refuser une transition
    path('planning/<uuid:planning_id>/transition/reject', views.reject_workflow_transition, name='reject_transition'),
    # Historique du workflow
    path('planning/<uuid:planning_id>/history', views.planning_workflow_history, name='workflow_history'),
    # Step actuel
    path('planning/<uuid:planning_id>/current-step', views.planning_current_step, name='current_step'),

]