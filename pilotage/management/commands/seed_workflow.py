from django.core.management.base import BaseCommand
from pilotage.models import Workflow, WorkflowStep, WorkflowTransition, WorkflowValidation
from security.models import Role
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Seed workflow data'

    def handle(self, *args, **kwargs):

        # ──  ROLES ──
        role_operateur, _ = Role.objects.get_or_create(
            code_role="OPERATEUR",
            defaults={"nom": "Opérateur de saisie"})
        role_gestionnaire, _ = Role.objects.get_or_create(
            code_role="GESTIONNAIRE",
            defaults={"nom": "Gestionnaire planification"})
        role_responsable, _ = Role.objects.get_or_create(
            code_role="RESPONSABLE",
            defaults={"nom": "Responsable exploitation"})
        role_ccr, _ = Role.objects.get_or_create(
            code_role="CCR",
            defaults={"nom": "Centre de Conduite des Réseaux"})

        self.stdout.write(" Roles créés")

        # ──  WORKFLOW ──
       
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()

        workflow, _ = Workflow.objects.get_or_create(
            code="TRAVAUX_PROGRAMMES",
            defaults={
                "name": "Workflow Travaux Programmés",
                "description": "Process complet des travaux programmés",
                "is_active": True,
                "created_by": admin
            }
        )

        self.stdout.write("Workflow créé")

        # ── STEPS ──
        steps_data = [
            {"number": 1,  "code": "CREATED",           "name": "Créé",                "is_terminal": False},
            {"number": 2,  "code": "SUBMITTED",          "name": "Soumis",              "is_terminal": False},
            {"number": 3,  "code": "ANALYZED",           "name": "Analysé",             "is_terminal": False},
            {"number": 4,  "code": "PLANNED_VALIDATED",  "name": "Planning validé",     "is_terminal": False},
            {"number": 5,  "code": "DDR_GENERATED",      "name": "DDR générée",         "is_terminal": False},
            {"number": 6,  "code": "CCR_APPROVED",       "name": "Approuvé CCR",        "is_terminal": False},
            {"number": 7,  "code": "CCR_REJECTED",       "name": "Refusé CCR",          "is_terminal": False},
            {"number": 8,  "code": "CCR_POSTPONED",      "name": "Reporté CCR",         "is_terminal": False},
            {"number": 9,  "code": "NAPT_GENERATED",     "name": "NAPT générée",        "is_terminal": False},
            {"number": 10, "code": "DIFFUSED",           "name": "Diffusé",             "is_terminal": False},
            {"number": 11, "code": "IN_PROGRESS",        "name": "En cours",            "is_terminal": False},
            {"number": 12, "code": "COMPLETED",          "name": "Terminé",             "is_terminal": False},
            {"number": 13, "code": "CLOSED",             "name": "Clôturé",             "is_terminal": True},
            {"number": 14, "code": "CANCELLED",          "name": "Annulé",              "is_terminal": True},
        ]

        steps = {}
        for s in steps_data:
            step, _ = WorkflowStep.objects.get_or_create(
                workflow=workflow,
                number=s['number'],
                defaults={
                    "code": s['code'],
                    "name": s['name'],
                    "is_terminal": s['is_terminal']
                }
            )
            steps[s['code']] = step

        self.stdout.write(" Steps créés")

        # ──  TRANSITIONS ──
        transitions_data = [
            {"name": "Soumettre",        "from": "CREATED",          "to": "SUBMITTED",         "can_go_back": False, "comment_required": False},
            {"name": "Analyser",         "from": "SUBMITTED",        "to": "ANALYZED",          "can_go_back": False, "comment_required": False},
            {"name": "Valider planning", "from": "ANALYZED",         "to": "PLANNED_VALIDATED", "can_go_back": False, "comment_required": False},
            {"name": "Générer DDR",      "from": "PLANNED_VALIDATED","to": "DDR_GENERATED",     "can_go_back": False, "comment_required": False},
            {"name": "Approuver CCR",    "from": "DDR_GENERATED",    "to": "CCR_APPROVED",      "can_go_back": False, "comment_required": False},
            {"name": "Refuser CCR",      "from": "DDR_GENERATED",    "to": "CCR_REJECTED",      "can_go_back": True,  "comment_required": True},
            {"name": "Reporter CCR",     "from": "DDR_GENERATED",    "to": "CCR_POSTPONED",     "can_go_back": True,  "comment_required": True},
            {"name": "Générer NAPT",     "from": "CCR_APPROVED",     "to": "NAPT_GENERATED",    "can_go_back": False, "comment_required": False},
            {"name": "Diffuser",         "from": "NAPT_GENERATED",   "to": "DIFFUSED",          "can_go_back": False, "comment_required": False},
            {"name": "Démarrer",         "from": "DIFFUSED",         "to": "IN_PROGRESS",       "can_go_back": False, "comment_required": False},
            {"name": "Terminer",         "from": "IN_PROGRESS",      "to": "COMPLETED",         "can_go_back": False, "comment_required": False},
            {"name": "Clôturer",         "from": "COMPLETED",        "to": "CLOSED",            "can_go_back": False, "comment_required": False},
            {"name": "Annuler",          "from": "CREATED",          "to": "CANCELLED",         "can_go_back": False, "comment_required": True},
            # Retours arrière
            {"name": "Retour soumission","from": "CCR_REJECTED",     "to": "SUBMITTED",         "can_go_back": True,  "comment_required": True},
            {"name": "Retour soumission","from": "CCR_POSTPONED",    "to": "SUBMITTED",         "can_go_back": True,  "comment_required": True},
        ]

        transitions = {}
        for t in transitions_data:
            transition, _ = WorkflowTransition.objects.get_or_create(
                workflow=workflow,
                from_step=steps[t['from']],
                to_step=steps[t['to']],
                defaults={
                    "name": t['name'],
                    "can_go_back": t['can_go_back'],
                    "comment_required": t['comment_required'],
                    "is_active": True
                }
            )
            transitions[f"{t['from']}__{t['to']}"] = transition

        self.stdout.write(" Transitions créées")

        # ──  VALIDATIONS (roles requis par transition) ──
        validations_data = [
            {"transition": "SUBMITTED__ANALYZED",           "role": role_gestionnaire},
            {"transition": "ANALYZED__PLANNED_VALIDATED",   "role": role_responsable},
            {"transition": "PLANNED_VALIDATED__DDR_GENERATED", "role": role_responsable},
            {"transition": "DDR_GENERATED__CCR_APPROVED",   "role": role_ccr},
            {"transition": "DDR_GENERATED__CCR_REJECTED",   "role": role_ccr},
            {"transition": "DDR_GENERATED__CCR_POSTPONED",  "role": role_ccr},
            {"transition": "NAPT_GENERATED__DIFFUSED",      "role": role_gestionnaire},
            {"transition": "COMPLETED__CLOSED",             "role": role_responsable},
        ]

        for v in validations_data:
            key = v['transition']
            if key in transitions:
                WorkflowValidation.objects.get_or_create(
                    transition=transitions[key],
                    role=v['role'],
                    step=transitions[key].from_step,
                )

        self.stdout.write(" Validations créées")
        self.stdout.write(self.style.SUCCESS(" Seed terminé avec succès !"))