from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


#  WORKFLOW
class Workflow(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name= "workflow_created_by")

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']


#  WORKFLOW STEP
class WorkflowStep(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="steps")
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_terminal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.workflow.name} - Step {self.number} : {self.name}"

    class Meta:
        ordering = ['number']
        unique_together = ('workflow', 'number')
        ordering = ['-created_at']


#  WORKFLOW TRANSITION

class WorkflowTransition(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="transitions")
    name = models.CharField(max_length=100)
    from_step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name="transition_sortantes", null=True, blank=True)
    to_step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name="transitions_entrantes",null=True, blank=True)
    can_go_back = models.BooleanField(default=False)
    comment_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        from_code = self.from_step.code if self.from_step else "START"
        to_code = self.to_step.code if self.to_step else "FINISH"
        return f"{self.name} : {from_code} -> {to_code}"
    
    class Meta:
        unique_together = ('workflow','from_step', 'to_step')
        ordering = ['-created_at']
       
       

#  WORKFLOW VALIDATION

class WorkflowValidation(models.Model):

    class Status(models.TextChoices):
        PENDING  = "PENDING",  _("En Attente")
        APPROVED = "APPROVED", _("Approuvé")
        REJECTED = "REJECTED", _("Rejeté")

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    transition = models.ForeignKey(WorkflowTransition, on_delete=models.CASCADE, related_name="validations")
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name="validations")
    role = models.ForeignKey('security.Role', on_delete=models.CASCADE, related_name="validations")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="validations_made")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    motif = models.TextField(blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transition} - {self.role} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']


#  WORKFLOW HISTORY

class WorkflowHistory(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    planning = models.ForeignKey('planning.Planning', on_delete=models.CASCADE, related_name="workflow_history")
    transition = models.ForeignKey(WorkflowTransition, on_delete=models.SET_NULL, null=True)
    from_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name="history_départ")
    to_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name="history_arrivé")
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    transitioned_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.planning} | {self.from_step} → {self.to_step}"

    class Meta:
        ordering = ['-transitioned_at']