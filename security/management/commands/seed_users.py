# security/commandes/management/commands/seed_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from security.models import Role, Permission, RolePermission, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed users, roles and permissions for testing'

    def handle(self, *args, **kwargs):

        #  1. PERMISSIONS 
        permissions_data = [
            # Users
            {"nom": "Gérer les utilisateurs", "code": "MANAGE_USERS"},
            # Roles
            {"nom": "Gérer les rôles", "code": "MANAGE_ROLES"},
            {"nom": "Gérer les permissions", "code": "MANAGE_PERMISSIONS"},
            # Workflow
            {"nom": "Gérer le workflow", "code": "MANAGE_WORKFLOW"},
            {"nom": "Exécuter une transition", "code": "WORKFLOW_TRANSITION"},
            {"nom": "Rejeter une transition", "code": "WORKFLOW_REJECT"},
            # Planning
            {"nom": "Créer un planning", "code": "CREATE_PLANNING"},
            {"nom": "Modifier un planning", "code": "UPDATE_PLANNING"},
            # DDR / NAPT
            {"nom": "Générer une DDR", "code": "GENERATE_DDR"},
            {"nom": "Décider sur une DDR", "code": "DECIDE_DDR"},
            {"nom": "Diffuser une NAPT", "code": "DIFFUSE_NAPT"},
        ]

        permissions = {}
        for p in permissions_data:
            perm, _ = Permission.objects.get_or_create(
                code=p['code'],
                defaults={"nom": p['nom']}
            )
            permissions[p['code']] = perm
        self.stdout.write("✅ Permissions créées")

        #  2. ROLES 
        roles_data = [
            {
                "nom": "Administrateur",
                "code_role": "ADMIN",
                "permissions": list(permissions.keys())  # toutes les permissions
            },
            {
                "nom": "Opérateur de saisie",
                "code_role": "OPERATEUR",
                "permissions": ["WORKFLOW_TRANSITION", "CREATE_PLANNING", "UPDATE_PLANNING"]
            },
            {
                "nom": "Gestionnaire planification",
                "code_role": "GESTIONNAIRE",
                "permissions": ["WORKFLOW_TRANSITION", "MANAGE_WORKFLOW", "DIFFUSE_NAPT"]
            },
            {
                "nom": "Responsable exploitation",
                "code_role": "RESPONSABLE",
                "permissions": ["WORKFLOW_TRANSITION", "WORKFLOW_REJECT", "GENERATE_DDR"]
            },
            {
                "nom": "Centre de Conduite des Réseaux",
                "code_role": "CCR",
                "permissions": ["DECIDE_DDR", "WORKFLOW_TRANSITION", "WORKFLOW_REJECT"]
            },
            {
                "nom": "Chargé de consignation",
                "code_role": "CHARGE_CONSIGNATION",
                "permissions": ["WORKFLOW_TRANSITION"]
            },
        ]

        roles = {}
        for r in roles_data:
            role, _ = Role.objects.get_or_create(
                code_role=r['code_role'],
                defaults={"nom": r['nom']}
            )
            roles[r['code_role']] = role

            # Assigner les permissions au rôle
            for code in r['permissions']:
                if code in permissions:
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permissions[code]
                    )
        self.stdout.write("✅ Rôles et permissions créés")

        #  3. USERS 
        users_data = [
            {
                "username": "admin",
                "first_name": "Admin",
                "last_name": "System",
                "email": "admin@maintenance.cm",
                "password": "Admin@1234",
                "role": "ADMIN",
                "is_superuser": True,
                "is_staff": True,
            },
            {
                "username": "operateur1",
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "operateur1@maintenance.cm",
                "password": "Operateur@1234",
                "role": "OPERATEUR",
            },
            {
                "username": "gestionnaire1",
                "first_name": "Marie",
                "last_name": "Martin",
                "email": "gestionnaire1@maintenance.cm",
                "password": "Gestionnaire@1234",
                "role": "GESTIONNAIRE",
            },
            {
                "username": "responsable1",
                "first_name": "Pierre",
                "last_name": "Bernard",
                "email": "responsable1@maintenance.cm",
                "password": "Responsable@1234",
                "role": "RESPONSABLE",
            },
            {
                "username": "ccr1",
                "first_name": "Sophie",
                "last_name": "Leclerc",
                "email": "ccr1@maintenance.cm",
                "password": "Ccr@1234",
                "role": "CCR",
            },
            {
                "username": "charge1",
                "first_name": "Paul",
                "last_name": "Durand",
                "email": "charge1@maintenance.cm",
                "password": "Charge@1234",
                "role": "CHARGE_CONSIGNATION",
            },
        ]

        for u in users_data:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    "first_name": u['first_name'],
                    "last_name": u['last_name'],
                    "email": u['email'],
                    "is_superuser": u.get('is_superuser', False),
                    "is_staff": u.get('is_staff', False),
                    "is_ldap": False,
                    "first_connection": False,
                }
            )
            if created:
                user.set_password(u['password'])
                user.save()

            # Assigner le rôle
            role = roles.get(u['role'])
            if role:
                UserRole.objects.get_or_create(user=user, role=role)

            status = "créé" if created else "déjà existant"
            self.stdout.write(f"  👤 {u['username']} ({u['role']}) → {status}")

        self.stdout.write("✅ Utilisateurs créés")
        self.stdout.write(self.style.SUCCESS("\n🎉 Seed users terminé avec succès !"))
        self.stdout.write("\n📋 Récapitulatif des comptes de test :")
        self.stdout.write("  admin          / Admin@1234        → Accès total")
        self.stdout.write("  operateur1     / Operateur@1234    → Crée les plannings")
        self.stdout.write("  gestionnaire1  / Gestionnaire@1234 → Analyse et diffuse")
        self.stdout.write("  responsable1   / Responsable@1234  → Valide et génère DDR")
        self.stdout.write("  ccr1           / Ccr@1234          → Décide sur les DDR")
        self.stdout.write("  charge1        / Charge@1234       → Chargé de consignation")