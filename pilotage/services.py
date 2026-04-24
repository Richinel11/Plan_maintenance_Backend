from django.utils import timezone
from .models import WorkflowTransition, WorkflowValidation, WorkflowHistory
from planning.models import PlanningTravaux
from security.models import UserRole


#  RÉCUPÉRER LES TRANSITIONS DISPONIBLES

def get_available_transitions(planning: PlanningTravaux):
    """
    Retourne les transitions disponibles pour un planning
    selon son current_step
    """
    if not planning.current_step:
        return WorkflowTransition.objects.none()

    return WorkflowTransition.objects.filter(from_step=planning.current_step,is_active=True).select_related('from_step', 'to_step')

# VÉRIFIER SI L'UTILISATEUR PEUT EFFECTUER LA TRANSITION

def can_user_transition(user, transition: WorkflowTransition) -> bool:
    """
    Vérifie si l'utilisateur a le rôle requis
    pour effectuer cette transition
    """
    # Récupère les rôles requis pour cette transition
    required_roles = WorkflowValidation.objects.filter(
        transition=transition,
        status=WorkflowValidation.Status.PENDING).values_list('role_id', flat=True)

    # Si aucun rôle requis, tout le monde peut effectuer la transition
    if not required_roles:
        return True

    # Vérifie si l'utilisateur a au moins un des rôles requis
    user_roles = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
    return any(role in user_roles for role in required_roles)

#  EXECUTER LA TRANSITION

def execute_transition(planning: PlanningTravaux, transition: WorkflowTransition, user, comment: str = "") -> dict:
    """
    Exécute une transition sur un planning :
    - Vérifie que la transition est valide
    - Vérifie les droits de l'utilisateur
    - Met à jour le current_step
    - Enregistre dans WorkflowHistory
    - Met à jour WorkflowValidation
    """

    #  Vérifier que la transition appartient au bon workflow
    if transition.workflow != planning.workflow:
        return {"success": False, "error": "Transition invalide pour ce workflow"}

    #  Vérifier que la transition part du bon step
    if transition.from_step != planning.current_step:
        return {"success": False, "error": "Transition invalide depuis l'étape actuelle"}

    #  Vérifier que la transition est active
    if not transition.is_active:
        return {"success": False, "error": "Transition inactive"}

    #  Vérifier les droits de l'utilisateur
    if not can_user_transition(user, transition):
        return {"success": False, "error": "Vous n'avez pas les droits pour effectuer cette transition"}

    #  Vérifier si un commentaire est requis
    if transition.comment_required and not comment:
        return {"success": False, "error": "Un commentaire est requis pour cette transition"}

    # Sauvegarder l'ancien step pour l'historique
    old_step = planning.current_step

    #  Mettre à jour le current_step du planning
    planning.current_step = transition.to_step
    planning.save(update_fields=['current_step', 'updated_at'])

    #  Enregistrer dans WorkflowHistory
    WorkflowHistory.objects.create(
        planning=planning,
        transition=transition,
        from_step=old_step,
        to_step=transition.to_step,
        performed_by=user,
        comment=comment
    )

    #  Mettre à jour la validation correspondante
    WorkflowValidation.objects.filter(
        transition=transition,
        status=WorkflowValidation.Status.PENDING).update(
        status=WorkflowValidation.Status.APPROVED,
        user=user,
        validated_at=timezone.now(),
        motif=comment
    )

    return {
        "success": True,
        "from_step": old_step,
        "to_step": transition.to_step
    }


# REFUSER UNE TRANSITION

def reject_transition(planning: PlanningTravaux, transition: WorkflowTransition, user, motif: str = "") -> dict:
    """
    Refuse une transition :
    - Vérifie les droits
    - Enregistre le refus dans WorkflowValidation (motif)
    - Enregistre dans WorkflowHistory
    - Remet le planning au step précédent si can_go_back=True
    """

    # Vérifier les droits
    if not can_user_transition(user, transition):
        return {"success": False, "error": "Vous n'avez pas les droits pour effectuer cette action"}

    # Mettre à jour la validation
    WorkflowValidation.objects.filter(
        transition=transition,
        status=WorkflowValidation.Status.PENDING).update(
        status=WorkflowValidation.Status.REJECTED,
        user=user,
        validated_at=timezone.now(),
        motif=motif
    )

    # Si can_go_back, on remet le planning au step précédent
    old_step = planning.current_step
    if transition.can_go_back:
        planning.current_step = transition.from_step
        planning.save(update_fields=['current_step', 'updated_at'])

    #  Enregistrer dans WorkflowHistory
    WorkflowHistory.objects.create(
        planning=planning,
        transition=transition,
        from_step=old_step,
        to_step=planning.current_step,
        performed_by=user,
        comment=motif
    )

    return {
        "success": False,
        "status": "REJECTED",
        "from_step": old_step,
        "to_step": planning.current_step,
        "motif": motif
    }



#  RÉCUPÉRER L'HISTORIQUE D'UN PLANNING

def get_planning_history(planning: PlanningTravaux):
    """
    Retourne l'historique complet des transitions d'un planning
    """
    return WorkflowHistory.objects.filter(planning=planning).select_related('from_step', 'to_step', 'performed_by', 'transition')