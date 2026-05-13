from django.core.management.base import BaseCommand
from ...models import Role, Permission, RolePermission

class Command(BaseCommand):
    help = 'Initialise les permissions et les assigne aux rôles'

    def handle(self, *args, **kwargs):

        # créer toutes les permissions
        permissions = [
            #permissions accordées aux roles
            {'code': 'CREATE_WORK',    'description': 'Créer un travail de maintenance'},
            {'code': 'UPDATE_WORK',    'description': 'Modifier un travail existant'},
            {'code': 'DELETE_WORK',    'description': 'Supprimer un travail'},
            {'code': 'VIEW_WORK',      'description': 'Consulter les travaux'},
            {'code': 'FOLLOW_WORK',     'description': 'Suivre l\'avancement des travaux'},
            {'code': 'END_WORK',        'description': 'Clôturer un travail'},
            {'code': 'VIEW_PLANNING',     'description': 'Consulter les plannings'},
            {'code': 'ALIGN_PLANNING',    'description': 'Proposer des alignements de planning'},
            {'code': 'VALIDATE_PLANNING', 'description': 'Valider un planning'},
            {'code': 'TRANSMIT_PLANNING', 'description': 'Transmettre un planning'},
            {'code': 'GENERATE_DDR',      'description': 'Générer une Demande de Retrait'},
            {'code': 'VIEW_DDR',          'description': 'Consulter les DDR'},
            {'code': 'APROVE_DDR',       'description': 'Approuver une DDR'},
            {'code': 'REFUSE_DDR',        'description': 'Refuser une DDR'},
            {'code': 'REPORT_DDR',        'description': 'Demander un report de DDR'},
            {'code': 'GENERATE_NAPT',     'description': 'Générer une NAPT'},
            {'code': 'VIEW_NAPT',         'description': 'Consulter les NAPT'},
            {'code': 'DIFFUSE_NAPT',      'description': 'Diffuser une NAPT'},
            {'code': 'VIEW_KPI',          'description': 'Consulter les indicateurs KPI'},
            {'code': 'VIEW_HISTORY',   'description': 'Consulter l\'historique complet'},
            {'code': 'VIEW_AUDIT',        'description': 'Accès lecture seule pour audit'},
            
            #permissions accordées à un utilisateur (admin)
            {'code':'CREATE_USER',      'description':'créer les utilisateurs'},
            {'code':'VIEW_USER',    'description':'voir tous les utilisateurs'},
            {'code': 'UPDATE_USER',     'description':'modifier un utilisateur'},
            {'code':'DELETE_USER',  'description':'supprimer un utilisateur'},
            {'code': 'RESTORE_USER',    'description':'restaurer un utilisateur'},
            {'code':'CREATE_ROLE',  'description':'créer un role'},
            {'code': 'UPDATE_ROLE',     'description':'modifier un role'},
            {'code': 'DELETE_ROLE',     'description':'enlever un role à un utilisateur'},
            {'code': 'ASSIGN_ROLE',     'description':'assigner un role à un utilisateur'},
            {'code': 'VIEW_ROLES',      'description':'voir tous les roles'},
            {'code': 'ASSIGN_PERMISSION',   'description':'assigner une permission à un role'},
            {'code': 'VIEWS_PERMISSIONS',   'description':'voir les permissions assignées à un role'},
            {'code':'MANAGE_PERMISSIONS',   'description':'gérer toutes les permissions'},
        ]

        for p in permissions:
            obj, created = Permission.objects.get_or_create(
                code=p['code'],
                defaults={
                    'nom': p['code'].replace('_', ' ').title(),
                    'description': p['description'],
                }
            )
            status = 'Créée' if created else ' Existe déjà'
            self.stdout.write(f"{status} : {obj.code}")

        #assigner les permissions aux rôles
        assignments = {
            'OPERATEUR_SAISIE': [
                'CREATE_WORK', 'UPDATE_WORK',
                'VIEW_WORK', 'FOLLOW_WORK', 'END_WORK',
            ],
            'GESTIONNAIRE_PLANNING': [
                'VIEW_WORK', 'FOLLOW_WORK',
                'VIEW_PLANNING', 'ALIGN_PLANNING', 'TRANSMIT_PLANNING',
            ],
            'RESPONSABLE_EXPLOITATION': [
                'VIEW_WORK', 'FOLLOW_WORK', 'END_WORK',
                'VIEW_PLANNING', 'VALIDATE_PLANNING',
                'GENERATE_DDR', 'VIEW_DDR',
            ],
            'CCR': [
                'VIEW_WORK', 'FOLLOW_WORK',
                'VIEW_PLANNING',
                'VIEW_DDR', 'APROVE_DDR', 'REFUSE_DDR', 'REPORT_DDR',
                'GENERATE_NAPT', 'VIEW_NAPT',
            ],
            'EQUIPE_COMMUNICATION': [
                'VIEW_NAPT', 'DIFFUSE_NAPT',
            ],
            'REGULATEUR': [
                'VIEW_WORK', 'VIEW_PLANNING',
                'VIEW_DDR', 'VIEW_NAPT',
                'VIEW_KPI', 'VIEW_HISTORY', 'VIEW_AUDIT',
            ],
            'ADMIN':[
                'CREATE_WORK', 'UPDATE_WORK','VIEW_WORK', 'FOLLOW_WORK', 'END_WORK', 
                'VIEW_PLANNING', 'ALIGN_PLANNING', 'TRANSMIT_PLANNING','VALIDATE_PLANNING',
                'GENERATE_DDR', 'DIFFUSE_NAPT','APROVE_DDR', 'REFUSE_DDR', 'REPORT_DDR',
                'GENERATE_NAPT', 'VIEW_NAPT','VIEW_DDR','VIEW_KPI', 'VIEW_HISTORY', 'VIEW_AUDIT',
                'CREATE_USER', 'VIEW_USER', 'UPDATE_USER', 'DELETE_USER', 'RESTORE_USER',
                'CREATE_ROLE', 'VIEW_ROLES', 'UPDATE_ROLE', 'DELETE_ROLE','ASSIGN_ROLE', 'VIEW_ROLES',
                'ASSIGN_PERMISSION','VIEWS_PERMISSIONS', 'MANAGE_PERMISSIONS'
            ]
        }

        for code_role, perms in assignments.items():
            try:
                role = Role.objects.get(code_role=code_role)
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Rôle introuvable : {code_role}"))
                continue

            for code_perm in perms:
                try:
                    permission = Permission.objects.get(code=code_perm)
                    _, created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
                    status = '✓' if created else '→'
                    self.stdout.write(f"  {status} {code_role} → {code_perm}")
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permission introuvable : {code_perm}"))

        self.stdout.write(self.style.SUCCESS('\nPermissions assignées avec succès !'))