from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from security.permission import HasPermission,HasPermissionFactory
from pilotage.services import (
    get_available_transitions,
    execute_transition,
    reject_transition,
    get_planning_history
)
from .serializers import (
    WorkflowSerializer, WorkflowWriteSerializer,
    WorkflowStepSerializer, WorkflowStepWriteSerializer,
    WorkflowTransitionSerializer, WorkflowTransitionWriteSerializer,
    WorkflowValidationSerializer, WorkflowValidationWriteSerializer,
    WorkflowHistorySerializer,
    ExecuteTransitionSerializer, RejectTransitionSerializer,
)
from planning.models import Planning
from .models import WorkflowTransition,Workflow,WorkflowHistory,WorkflowStep,WorkflowValidation

# WORKFLOW CRUD

@extend_schema(
    tags=["Pilotage"],
    request=WorkflowWriteSerializer,
    responses={200: WorkflowSerializer(many=True), 201: WorkflowSerializer, 400: {"type": "object"}},
    description="Lister tous les workflows (GET) ou créer un nouveau workflow (POST)"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def workflow_list_create(request):
    #lister les workflows
    
    if request.method == 'GET':
        workflows = Workflow.objects.all()
        serializer = WorkflowSerializer(workflows, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    #creer un workflow
    
    if request.method == 'POST':
        serializer = WorkflowWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Pilotage"],
    request=WorkflowWriteSerializer,
    responses={200: WorkflowSerializer, 204: None, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Récupérer, modifier ou supprimer un workflow"
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def workflow_detail(request, workflow_id):
    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        return Response({"error": "Workflow introuvable"},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkflowSerializer(workflow)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = WorkflowWriteSerializer(workflow, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        workflow.delete()
        return Response(
            {"message": "Workflow supprimé avec succès"},
            status=status.HTTP_204_NO_CONTENT
        )


# WORKFLOW STEP CRUD

@extend_schema(
    tags=["Pilotage"],
    request=WorkflowStepWriteSerializer,
    responses={200: WorkflowStepSerializer(many=True), 201: WorkflowStepSerializer, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Lister les steps d'un workflow (GET) ou en créer un (POST)"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def step_list_create(request, workflow_id):
    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        return Response({"error": "Workflow introuvable"},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        steps = WorkflowStep.objects.filter(workflow=workflow)
        serializer = WorkflowStepSerializer(steps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = WorkflowStepWriteSerializer(data=request.data, context={'workflow': workflow})
        if serializer.is_valid():
            serializer.save(workflow=workflow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Pilotage"],
    request=WorkflowStepWriteSerializer,
    responses={200: WorkflowStepSerializer, 204: None, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Récupérer, modifier ou supprimer un step"
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def step_detail(request, workflow_id, step_id):
    try:
        step = WorkflowStep.objects.get(id=step_id, workflow__id=workflow_id)
    except WorkflowStep.DoesNotExist:
        return Response({"error": "Step introuvable"},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkflowStepSerializer(step)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = WorkflowStepWriteSerializer(step, data=request.data, partial=True, context={'workflow': step.workflow})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        step.delete()
        return Response({"message": "Step supprimé avec succès"},status=status.HTTP_204_NO_CONTENT)


# WORKFLOW TRANSITION CRUD

@extend_schema(
    tags=["Pilotage"],
    request=WorkflowTransitionWriteSerializer,
    responses={200: WorkflowTransitionSerializer(many=True), 201: WorkflowTransitionSerializer, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Lister les transitions d'un workflow (GET) ou en créer une (POST)"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def transition_list_create(request, workflow_id):
    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        return Response({"error": "Workflow introuvable"},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        transitions = WorkflowTransition.objects.filter(workflow=workflow)
        serializer = WorkflowTransitionSerializer(transitions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = WorkflowTransitionWriteSerializer(data=request.data, context={'workflow': workflow})
        if serializer.is_valid():
            serializer.save(workflow=workflow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Pilotage"],
    request=WorkflowTransitionWriteSerializer,
    responses={200: WorkflowTransitionSerializer, 204: None, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Récupérer, modifier ou supprimer une transition"
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def transition_detail(request, workflow_id, transition_id):
    try:
        transition = WorkflowTransition.objects.get(id=transition_id, workflow__id=workflow_id)
    except WorkflowTransition.DoesNotExist:
        return Response({"error": "Transition introuvable"},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkflowTransitionSerializer(transition)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = WorkflowTransitionWriteSerializer(transition, data=request.data, partial=True, context={'workflow': transition.workflow})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        transition.delete()
        return Response({"message": "Transition supprimée avec succès"}, status=status.HTTP_204_NO_CONTENT)



# WORKFLOW VALIDATION CRUD

@extend_schema(
    tags=["Pilotage"],
    request=WorkflowValidationWriteSerializer,
    responses={200: WorkflowValidationSerializer(many=True), 201: WorkflowValidationSerializer, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Lister les validations d'une transition (GET) ou en créer une (POST)"
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def validation_list_create(request, transition_id):
    try:
        transition = WorkflowTransition.objects.get(id=transition_id)
    except WorkflowTransition.DoesNotExist:
        return Response({"error": "Transition introuvable"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        validations = WorkflowValidation.objects.filter(transition=transition)
        serializer = WorkflowValidationSerializer(validations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = WorkflowValidationWriteSerializer(data=request.data, context={'transition': transition})
        if serializer.is_valid():
            serializer.save(transition=transition)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Pilotage"],
    request=WorkflowValidationWriteSerializer,
    responses={200: WorkflowValidationSerializer, 204: None, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Récupérer, modifier ou supprimer une validation"
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, HasPermissionFactory('MANAGE_WORKFLOW')])
def validation_detail(request, transition_id, validation_id):
    try:
        validation = WorkflowValidation.objects.get(id=validation_id, transition__id=transition_id)
    except WorkflowValidation.DoesNotExist:
        return Response({"error": "Validation introuvable"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkflowValidationSerializer(validation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PUT':
        serializer = WorkflowValidationWriteSerializer(validation, data=request.data, partial=True, context={'transition': validation.transition})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        validation.delete()
        return Response({"message": "Validation supprimée avec succès"},status=status.HTTP_204_NO_CONTENT)


# VOIR LES TRANSITIONS DISPONIBLES POUR UN PLANNING

@extend_schema(
    tags=["Pilotage"],
    responses={200: WorkflowTransitionSerializer(many=True), 404: {"type": "object"}},
    description="Retourner les transitions disponibles pour un planning"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_transitions(request, planning_id):
    """
    Retourne les transitions disponibles pour un planning
    """
    try:
        planning = Planning.objects.get(id=planning_id)
    except Planning.DoesNotExist:
        return Response({"error": "Planning introuvable"},status=status.HTTP_404_NOT_FOUND)

    transitions = get_available_transitions(planning)
    serializer = WorkflowTransitionSerializer(transitions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

#  EXECUTER UNE TRANSITION

@extend_schema(
    tags=["Pilotage"],
    request=ExecuteTransitionSerializer,
    responses={200: {"type": "object"}, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Exécuter une transition sur un planning"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('WORKFLOW_TRANSITION')])
def execute_workflow_transition(request, planning_id):
    """
    Exécute une transition sur un planning
    Body: { "transition_id": "...", "comment": "..." }
    """
    try:
        planning = Planning.objects.get(id=planning_id)
    except Planning.DoesNotExist:
        return Response({"error": "Planning introuvable"},status=status.HTTP_404_NOT_FOUND)

    transition_id = request.data.get('transition_id')
    comment = request.data.get('comment', '')

    if not transition_id:
        return Response({"error": "transition_id est requis"},status=status.HTTP_400_BAD_REQUEST)

    try:
        transition = WorkflowTransition.objects.get(id=transition_id)
    except WorkflowTransition.DoesNotExist:
        return Response({"error": "Transition introuvable"},status=status.HTTP_404_NOT_FOUND)

    result = execute_transition(planning, transition, request.user, comment)

    if not result['success']:
        return Response({"error": result['error']},status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_200_OK)

#  REFUSER UNE TRANSITION
@extend_schema(
    tags=["Pilotage"],
    request=RejectTransitionSerializer,
    responses={200: {"type": "object"}, 400: {"type": "object"}, 404: {"type": "object"}},
    description="Refuser une transition sur un planning"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermissionFactory('WORKFLOW_REJECT')])
def reject_workflow_transition(request, planning_id):
    """
    Refuse une transition sur un planning
    Body: { "transition_id": "...", "motif": "..." }
    """
    try:
        planning = Planning.objects.get(id=planning_id)
    except Planning.DoesNotExist:
        return Response({"error": "Planning introuvable"},status=status.HTTP_404_NOT_FOUND)

    transition_id = request.data.get('transition_id')
    motif = request.data.get('motif', '')

    if not transition_id:
        return Response({"error": "transition_id est requis"},status=status.HTTP_400_BAD_REQUEST)

    try:
        transition = WorkflowTransition.objects.get(id=transition_id)
    except WorkflowTransition.DoesNotExist:
        return Response({"error": "Transition introuvable"},status=status.HTTP_404_NOT_FOUND)

    result = reject_transition(planning, transition, request.user, motif)

    return Response(result, status=status.HTTP_200_OK)


#  HISTORIQUE D'UN PLANNING
@extend_schema(
    tags=["Pilotage"],
    responses={200: WorkflowHistorySerializer(many=True), 404: {"type": "object"}},
    description="Retourner l'historique complet des transitions d'un planning"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def planning_workflow_history(request, planning_id):
    """
    Retourne l'historique complet des transitions d'un planning
    """
    try:
        planning = Planning.objects.get(id=planning_id)
    except Planning.DoesNotExist:
        return Response({"error": "Planning introuvable"},status=status.HTTP_404_NOT_FOUND)

    history = get_planning_history(planning)
    serializer = WorkflowHistorySerializer(history, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


#  CURRENT STEP D'UN PLANNING

@extend_schema(
    tags=["Pilotage"],
    responses={200: {"type": "object"}, 404: {"type": "object"}},
    description="Retourner le step actuel d'un planning"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def planning_current_step(request, planning_id):
    """
    Retourne le step actuel d'un planning
    """
    try:
        planning = Planning.objects.select_related('current_step', 'workflow').get(id=planning_id)
    except Planning.DoesNotExist:
        return Response({"error": "Planning introuvable"},status=status.HTTP_404_NOT_FOUND)

    return Response({
        "planning_id": str(planning.id),
        "workflow": planning.workflow.name if planning.workflow else None,
        "current_step": {
            "code": planning.current_step.code if planning.current_step else None,
            "name": planning.current_step.name if planning.current_step else None,
            "number": planning.current_step.number if planning.current_step else None,
        }
    }, status=status.HTTP_200_OK)