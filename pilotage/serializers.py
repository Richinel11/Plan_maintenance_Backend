from rest_framework import serializers
from .models import Workflow, WorkflowStep, WorkflowTransition, WorkflowValidation, WorkflowHistory


# WORKFLOW STEP SERIALIZER
class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ['id', 'number', 'name', 'code', 'description', 'is_terminal']



#  WORKFLOW SERIALIZER

class WorkflowSerializer(serializers.ModelSerializer):
    steps = WorkflowStepSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = ['id', 'name', 'code', 'description', 'is_active', 'steps', 'created_at']

#pour l'affichage du workflow dans le plannig
 
class WorkflowShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'code']


#  WORKFLOW TRANSITION SERIALIZER

class WorkflowTransitionSerializer(serializers.ModelSerializer):
    from_step = WorkflowStepSerializer(read_only=True)
    to_step = WorkflowStepSerializer(read_only=True)

    class Meta:
        model = WorkflowTransition
        fields = [
            'id', 'name', 'from_step', 'to_step',
            'can_go_back', 'comment_required', 'is_active'
        ]



#  WORKFLOW VALIDATION SERIALIZER

class WorkflowValidationSerializer(serializers.ModelSerializer):
    transition = WorkflowTransitionSerializer(read_only=True)
    step = WorkflowStepSerializer(read_only=True)
    role_name = serializers.CharField(source='role.nom', read_only=True)
    performed_by = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = WorkflowValidation
        fields = [
            'id', 'transition', 'step', 'role_name',
            'performed_by', 'status', 'motif',
            'validated_at', 'created_at'
        ]



#  WORKFLOW HISTORY SERIALIZER

class WorkflowHistorySerializer(serializers.ModelSerializer):
    from_step = WorkflowStepSerializer(read_only=True)
    to_step = WorkflowStepSerializer(read_only=True)
    transition_name = serializers.CharField(source='transition.name', read_only=True)
    performed_by = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowHistory
        fields = [
            'id', 'transition_name', 'from_step', 'to_step',
            'performed_by', 'comment', 'transitioned_at'
        ]

    def get_performed_by(self, obj):
        if obj.performed_by:
            return {
                "id": str(obj.performed_by.id),
                "full_name": obj.performed_by.get_full_name(),
                "username": obj.performed_by.username
            }
        return None
    
    

# WRITE SERIALIZERS

class WorkflowWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'code', 'description', 'is_active']

    def validate_code(self, value):
        # Vérifier l'unicité du code en excluant l'instance actuelle (update)
        qs = Workflow.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Un workflow avec ce code existe déjà.")
        return value.upper()  # forcer le code en majuscule


class WorkflowStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ['id', 'number', 'name', 'code', 'description', 'is_terminal']

    def validate(self, attrs):
        # Vérifier l'unicité du number dans le workflow
        workflow = self.context.get('workflow')
        number = attrs.get('number')
        qs = WorkflowStep.objects.filter(workflow=workflow, number=number)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(
                {"number": f"Le step numéro {number} existe déjà dans ce workflow."}
            )
        return attrs

    def validate_code(self, value):
        return value.upper()


class WorkflowTransitionWriteSerializer(serializers.ModelSerializer):
    from_step = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowStep.objects.all(),
        allow_null=True,
        required=False
    )
    to_step = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowStep.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = WorkflowTransition
        fields = ['id', 'name', 'from_step', 'to_step','can_go_back', 'comment_required', 'is_active']

    def validate(self, attrs):
        workflow = self.context.get('workflow')
        from_step = attrs.get('from_step')
        to_step = attrs.get('to_step')

        # Vérifier que from_step et to_step appartiennent au même workflow
        if from_step and from_step.workflow != workflow:
            raise serializers.ValidationError(
                {"from_step": "Ce step n'appartient pas à ce workflow."}
            )
        if to_step and to_step.workflow != workflow:
            raise serializers.ValidationError(
                {"to_step": "Ce step n'appartient pas à ce workflow."}
            )

        # Vérifier l'unicité de la transition
        qs = WorkflowTransition.objects.filter(workflow=workflow, from_step=from_step,to_step=to_step)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Une transition entre ces deux steps existe déjà.")

        return attrs


class WorkflowValidationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowValidation
        fields = ['id', 'step', 'role', 'status', 'motif']

    def validate_step(self, value):
        # Vérifier que le step appartient au même workflow que la transition
        transition = self.context.get('transition')
        if transition and value.workflow != transition.workflow:
            raise serializers.ValidationError("Ce step n'appartient pas au workflow de cette transition.")
        return value


class ExecuteTransitionSerializer(serializers.Serializer):
    transition_id = serializers.UUIDField()
    comment = serializers.CharField(required=False, allow_blank=True)


class RejectTransitionSerializer(serializers.Serializer):
    transition_id = serializers.UUIDField()
    motif = serializers.CharField(required=False, allow_blank=True)