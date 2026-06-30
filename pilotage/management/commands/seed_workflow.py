from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pilotage.models import Workflow, WorkflowStep, WorkflowTransition, WorkflowValidation
from security.models import Role


STEPS_DATA = [
    {
        "number": 1,
        "code": "CREER",
        "name": "Créer",
        "is_terminal": False,
        "description": (
            "Planning créé ou importé par l'opérateur de saisie. "
            "Le gestionnaire de planification peut harmoniser les travaux avant de valider."
        ),
    },
    {
        "number": 2,
        "code": "EN_ATTENTE",
        "name": "En attente",
        "is_terminal": False,
        "description": (
            "Planning validé par le gestionnaire. Le responsable génère les DDR "
            "pour les travaux concernés. Avance automatiquement quand toutes les DDR "
            "générées sont à l'état COMPLÉTÉE."
        ),
    },
    {
        "number": 3,
        "code": "COMPLETE",
        "name": "Complété",
        "is_terminal": False,
        "description": (
            "Toutes les DDR du planning sont complètes. Le CCR traite les DDR "
            "et génère les NAPT. Avance automatiquement quand toutes les NAPT "
            "générées sont à l'état DIFFUSÉE."
        ),
    },
    {
        "number": 4,
        "code": "VALIDE",
        "name": "Validé",
        "is_terminal": False,
        "description": (
            "Toutes les NAPT du planning sont diffusées. Les travaux peuvent démarrer "
            "sur le terrain. Un utilisateur marque manuellement le planning comme terminé."
        ),
    },
    {
        "number": 5,
        "code": "TERMINE",
        "name": "Terminé",
        "is_terminal": True,
        "description": "Tous les travaux du planning sont terminés. Planning clôturé — état final.",
    },
]

TRANSITIONS_DATA = [
    {
        "name": "Valider",
        "from": "CREER",
        "to": "EN_ATTENTE",
        "can_go_back": False,
        "comment_required": False,
        "role_code": "GESTIONNAIRE",
    },
    {
        "name": "Retourner pour correction",
        "from": "EN_ATTENTE",
        "to": "CREER",
        "can_go_back": True,
        "comment_required": True,
        "role_code": "GESTIONNAIRE",
    },
    {
        # Déclenchée automatiquement quand toutes les DDR
        # du planning sont à l'état COMPLÉTÉE
        "name": "DDR complètes (auto)",
        "from": "EN_ATTENTE",
        "to": "COMPLETE",
        "can_go_back": False,
        "comment_required": False,
        "role_code": None,
    },
    {
        # Déclenchée automatiquement quand toutes les NAPT
        # du planning sont à l'état DIFFUSÉE
        "name": "NAPT diffusées (auto)",
        "from": "COMPLETE",
        "to": "VALIDE",
        "can_go_back": False,
        "comment_required": False,
        "role_code": None,
    },
    {
        "name": "Terminer",
        "from": "VALIDE",
        "to": "TERMINE",
        "can_go_back": False,
        "comment_required": False,
        "role_code": "RESPONSABLE",
    },
]


class Command(BaseCommand):
    help = "Seed le workflow TRAVAUX_PROGRAMMES (5 étapes, niveau planning)"

    def handle(self, *args, **kwargs):

        # ── SUPERUTILISATEUR requis par Workflow.created_by ──────────
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stderr.write(self.style.ERROR(
                "[ERREUR] Aucun superutilisateur trouve. "
                "Creez-en un avec `createsuperuser` d'abord."
            ))
            return

        # ── WORKFLOW ─────────────────────────────────────────────────
        workflow, wf_created = Workflow.objects.get_or_create(
            code="TRAVAUX_PROGRAMMES",
            defaults={
                "name": "Travaux Programmés",
                "description": (
                    "Cycle de vie d'un planning de travaux programmés : "
                    "du dépôt par l'opérateur jusqu'à la clôture finale."
                ),
                "is_active": True,
                "created_by": admin,
            }
        )
        self._log(wf_created, f"Workflow : {workflow.name} (code={workflow.code})")

        # ── NETTOYAGE des anciennes transitions et steps ─────────────
        # Nécessaire si le workflow existait déjà avec d'anciens steps
        if not wf_created:
            old_transitions = WorkflowTransition.objects.filter(workflow=workflow).count()
            old_steps = WorkflowStep.objects.filter(workflow=workflow).count()
            WorkflowTransition.objects.filter(workflow=workflow).delete()
            WorkflowStep.objects.filter(workflow=workflow).delete()
            self.stdout.write(
                f"  [nettoyage] Supprime : {old_transitions} transition(s) et {old_steps} step(s) anciens"
            )

        # ── STEPS ────────────────────────────────────────────────────
        steps = {}
        for s in STEPS_DATA:
            step = WorkflowStep.objects.create(
                workflow=workflow,
                number=s["number"],
                code=s["code"],
                name=s["name"],
                is_terminal=s["is_terminal"],
                description=s["description"],
            )
            steps[s["code"]] = step
            self.stdout.write(
                self.style.SUCCESS(f"  [+] Step {s['number']} : {s['name']} ({s['code']})")
            )

        # ── TRANSITIONS ──────────────────────────────────────────────
        for t in TRANSITIONS_DATA:
            transition = WorkflowTransition.objects.create(
                workflow=workflow,
                name=t["name"],
                from_step=steps[t["from"]],
                to_step=steps[t["to"]],
                can_go_back=t["can_go_back"],
                comment_required=t["comment_required"],
                is_active=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [+] Transition : {t['from']} -> {t['to']}  ({t['name']})"
                )
            )

            # Associer le rôle requis via WorkflowValidation
            if t["role_code"]:
                try:
                    role = Role.objects.get(code_role=t["role_code"])
                    WorkflowValidation.objects.create(
                        transition=transition,
                        role=role,
                        step=steps[t["from"]],
                    )
                    self.stdout.write(f"        -> Role requis : {role.nom}")
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"        [!] Role '{t['role_code']}' introuvable — "
                            "lancez seed_all d'abord."
                        )
                    )

        # ── RÉPARATION des plannings orphelins ───────────────────────
        # Supprimer puis recréer les steps met current_step à NULL
        # (FK on_delete=SET_NULL). On réinitialise donc tout planning
        # rattaché à ce workflow mais sans étape → étape de départ CREER.
        from planning.models import Planning
        orphelins = Planning.objects.filter(
            workflow=workflow, current_step__isnull=True
        )
        nb_repares = orphelins.update(current_step=steps["CREER"])
        if nb_repares:
            self.stdout.write(
                self.style.WARNING(
                    f"  [repare] {nb_repares} planning(s) orphelin(s) reinitialise(s) a l'etape CREER"
                )
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("[OK] Seed workflow termine."))
        self.stdout.write("")
        self.stdout.write("Recapitulatif TRAVAUX_PROGRAMMES :")
        self.stdout.write("  [1] CREER       --(Gestionnaire valide)----> [2] EN_ATTENTE")
        self.stdout.write("  [2] EN_ATTENTE  --(DDR completes, auto)----> [3] COMPLETE")
        self.stdout.write("  [3] COMPLETE    --(NAPT diffusees, auto)---> [4] VALIDE")
        self.stdout.write("  [4] VALIDE      --(Terminer, manuel)-------> [5] TERMINE")
        self.stdout.write("  [2] EN_ATTENTE  --(Retourner, motif requis)> [1] CREER")

    def _log(self, created, label):
        if created:
            self.stdout.write(self.style.SUCCESS(f"  [+] {label}"))
        else:
            self.stdout.write(f"  [ ] {label} (deja existant, nettoyage en cours...)")
