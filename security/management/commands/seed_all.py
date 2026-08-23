# security/management/commands/seed_all.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed complet de toutes les données de test'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n🚀 Démarrage du seed complet...\n'))
        self._seed_entites_metier()
        self._seed_unites_demanderesses()
        self._seed_permissions()
        self._seed_roles()
        self._seed_users()
        #self._seed_referentiel()
        self._seed_types_activite()
        self._seed_workflow()
        self._seed_plannings_et_travaux()
        self._seed_scenarios_harmonisation()
        self.stdout.write(self.style.SUCCESS('\n🎉 Seed complet terminé avec succès !\n'))
        self._print_recap()

    # ─────────────────────────────────────────
    # 1. ENTITÉS MÉTIER
    # ─────────────────────────────────────────
    def _seed_entites_metier(self):
        from user.models import EntiteMetier

        entites = [
            {"name": "Production",    "type": "PROD"},
            {"name": "Transport",     "type": "TRANS"},
            {"name": "Distribution",  "type": "DIST"},
        ]
        for e in entites:
            EntiteMetier.objects.get_or_create(
                name=e['name'], defaults={"type": e['type']}
            )
        self.stdout.write("✅ Entités métier créées")

    # ─────────────────────────────────────────
    # 2. UNITÉS DEMANDERESSES
    # ─────────────────────────────────────────
    def _seed_unites_demanderesses(self):
        from user.models import EntiteMetier, UniteDemanderesse

        prod  = EntiteMetier.objects.get(name="Production")
        trans = EntiteMetier.objects.get(name="Transport")
        dist  = EntiteMetier.objects.get(name="Distribution")

        unites = [
            # PRODUCTION
            {"nom": "DCP Songloulou",   "entite": prod},
            {"nom": "DCP Edéa",         "entite": prod},
            {"nom": "DCP Lagdo",        "entite": prod},
            {"nom": "IPP NHPC",         "entite": prod},
            {"nom": "IPP KPDC",         "entite": prod},
            {"nom": "IPP DPDC",         "entite": prod},
            # TRANSPORT
            {"nom": "Transport Centre-Sud-Est",              "entite": trans},
            {"nom": "Transport Littoral-Sud Ouest",          "entite": trans},
            {"nom": "Transport Ouest Nord Ouest",            "entite": trans},
            {"nom": "Transport Nord-Extrême Nord-Adamaoua",  "entite": trans},
            # DISTRIBUTION
            {"nom": "Distribution Poste source",             "entite": dist},
            {"nom": "Exploitation Douala Nord",              "entite": dist},
            {"nom": "Exploitation Douala Sud",               "entite": dist},
            {"nom": "Exploitation Douala Ouest",             "entite": dist},
            {"nom": "Exploitation Douala Est",               "entite": dist},
            {"nom": "Exploitation Douala Centre",            "entite": dist},
            {"nom": "Exploitation Yaoundé Nord",             "entite": dist},
            {"nom": "Exploitation Yaoundé Sud",              "entite": dist},
            {"nom": "Exploitation Yaoundé Centre",           "entite": dist},
            {"nom": "Exploitation technique Centre",         "entite": dist},
            {"nom": "Exploitation technique Sud Mbalmayo",   "entite": dist},
            {"nom": "Exploitation technique Est",            "entite": dist},
            {"nom": "Exploitation technique Ouest Nord Ouest","entite": dist},
            {"nom": "Exploitation technique Sanaga Océan",   "entite": dist},
            {"nom": "Exploitation technique Nord",           "entite": dist},
            {"nom": "Exploitation technique Extrême-Nord",   "entite": dist},
            {"nom": "Exploitation technique Adamaoua",       "entite": dist},
            {"nom": "Exploitation technique Sud Ouest Moungo","entite": dist},
        ]
        for u in unites:
            UniteDemanderesse.objects.get_or_create(
                nom=u['nom'], defaults={"entite_metier": u['entite']}
            )
        self.stdout.write("✅ Unités demanderesses créées")

    # ─────────────────────────────────────────
    # 3. PERMISSIONS
    # ─────────────────────────────────────────
    def _seed_permissions(self):
        from security.models import Permission

        permissions = [
            # Module PLAN
            {"nom": "Gérer les utilisateurs",      "code": "MANAGE_USERS",       "module": "PLAN"},
            {"nom": "Gérer les rôles",             "code": "MANAGE_ROLES",       "module": "PLAN"},
            {"nom": "Gérer les permissions",       "code": "MANAGE_PERMISSIONS", "module": "PLAN"},
            {"nom": "Gérer le workflow",           "code": "MANAGE_WORKFLOW",    "module": "PLAN"},
            {"nom": "Exécuter une transition",     "code": "WORKFLOW_TRANSITION","module": "PLAN"},
            {"nom": "Rejeter une transition",      "code": "WORKFLOW_REJECT",    "module": "PLAN"},
            {"nom": "Créer un planning",           "code": "CREATE_PLANNING",    "module": "PLAN"},
            {"nom": "Modifier un planning",        "code": "UPDATE_PLANNING",    "module": "PLAN"},
            {"nom": "Créer un travail",            "code": "CREATE_TRAVAIL",     "module": "PLAN"},
            {"nom": "Modifier un travail",         "code": "UPDATE_TRAVAIL",     "module": "PLAN"},
            {"nom": "Analyser chevauchements",     "code": "ANALYSE_CHEVAUCHEMENTS","module": "PLAN"},
            # Module DDR
            {"nom": "Générer une DDR",             "code": "GENERATE_DDR",       "module": "DDR"},
            {"nom": "Décider sur une DDR",         "code": "DECIDE_DDR",         "module": "DDR"},
            # Module NAPT
            {"nom": "Diffuser une NAPT",           "code": "DIFFUSE_NAPT",       "module": "NAPT"},
        ]
        perms = {}
        for p in permissions:
            perm, _ = Permission.objects.get_or_create(
                code=p['code'],
                defaults={"nom": p['nom'], "module": p['module']}
            )
            perms[p['code']] = perm

        self.stdout.write("✅ Permissions créées")
        return perms

    # ─────────────────────────────────────────
    # 4. RÔLES
    # ─────────────────────────────────────────
    def _seed_roles(self):
        from security.models import Role, Permission, RolePermission

        roles_data = [
            {
                "nom": "Administrateur",
                "code_role": "ADMIN",
                "permissions": [
                    "MANAGE_USERS", "MANAGE_ROLES", "MANAGE_PERMISSIONS",
                    "MANAGE_WORKFLOW", "WORKFLOW_TRANSITION", "WORKFLOW_REJECT",
                    "CREATE_PLANNING", "UPDATE_PLANNING", "CREATE_TRAVAIL",
                    "UPDATE_TRAVAIL", "ANALYSE_CHEVAUCHEMENTS",
                    "GENERATE_DDR", "DECIDE_DDR", "DIFFUSE_NAPT"
                ]
            },
            {
                "nom": "Opérateur de saisie",
                "code_role": "OPERATEUR",
                "permissions": [
                    "CREATE_PLANNING", "UPDATE_PLANNING",
                    "CREATE_TRAVAIL", "UPDATE_TRAVAIL",
                    "WORKFLOW_TRANSITION"
                ]
            },
            {
                "nom": "Gestionnaire planification",
                "code_role": "GESTIONNAIRE",
                "permissions": [
                    "WORKFLOW_TRANSITION", "MANAGE_WORKFLOW",
                    "ANALYSE_CHEVAUCHEMENTS", "DIFFUSE_NAPT"
                ]
            },
            {
                "nom": "Responsable exploitation",
                "code_role": "RESPONSABLE",
                "permissions": [
                    "WORKFLOW_TRANSITION", "WORKFLOW_REJECT", "GENERATE_DDR"
                ]
            },
            {
                "nom": "Centre de Conduite des Réseaux",
                "code_role": "CCR",
                "permissions": [
                    "DECIDE_DDR", "WORKFLOW_TRANSITION", "WORKFLOW_REJECT"
                ]
            },
            {
                "nom": "Chargé de consignation",
                "code_role": "CHARGE_CONSIGNATION",
                "permissions": ["WORKFLOW_TRANSITION"]
            },
        ]

        for r in roles_data:
            # Le code d'un rôle a pu évoluer dans une base déjà initialisée.
            # ``nom`` et ``code_role`` sont tous deux uniques : un simple
            # get_or_create(code_role=...) tente alors de recréer un nom qui
            # existe déjà, ce qui provoque une erreur d'unicité.
            role = Role.objects.filter(code_role=r['code_role']).first()
            if role is None:
                role = Role.objects.filter(nom=r['nom']).first()
                if role is None:
                    role = Role.objects.create(
                        code_role=r['code_role'], nom=r['nom']
                    )
                else:
                    # On conserve le même rôle (et donc ses utilisateurs et
                    # permissions), en le mettant au code attendu par le seed.
                    role.code_role = r['code_role']
                    role.save(update_fields=['code_role'])
            for code in r['permissions']:
                try:
                    perm = Permission.objects.get(code=code)
                    RolePermission.objects.get_or_create(role=role, permission=perm)
                except Permission.DoesNotExist:
                    pass

        self.stdout.write("✅ Rôles et permissions créés")

    # ─────────────────────────────────────────
    # 5. UTILISATEURS
    # ─────────────────────────────────────────
    def _seed_users(self):
        from security.models import Role, UserRole
        from user.models import EntiteMetier

        prod  = EntiteMetier.objects.get(name="Production")
        trans = EntiteMetier.objects.get(name="Transport")
        dist  = EntiteMetier.objects.get(name="Distribution")

        users_data = [
            {
                "username": "admin",
                "first_name": "Admin", "last_name": "System",
                "email": "admin@maintenance.cm",
                "password": "Admin@1234",
                "role": "ADMIN",
                "entite": None,
                "is_superuser": True, "is_staff": True,
            },
            {
                "username": "operateur1",
                "first_name": "ekane", "last_name": "dominique",
                "email": "operateur1@maintenance.cm",
                "password": "Operateur@1234",
                "role": "OPERATEUR",
                "entite": dist,
            },
            {
                "username": "operateur2",
                "first_name": "Paula", "last_name": "Ngassa",
                "email": "operateur2@maintenance.cm",
                "password": "Operateur@1234",
                "role": "OPERATEUR",
                "entite": trans,
            },
            {
                "username": "gestionnaire1",
                "first_name": "Marie", "last_name": "logan II",
                "email": "gestionnaire1@maintenance.cm",
                "password": "Gestionnaire@1234",
                "role": "GESTIONNAIRE",
                "entite": dist,
            },
            {
                "username": "responsable1",
                "first_name": "Pierre", "last_name": "Bernard",
                "email": "responsable1@maintenance.cm",
                "password": "Responsable@1234",
                "role": "RESPONSABLE",
                "entite": dist,
            },
            {
                "username": "ccr1",
                "first_name": "Sophie", "last_name": "Leclerc",
                "email": "ccr1@maintenance.cm",
                "password": "Ccr@1234",
                "role": "CCR",
                "entite": None,
            },
            {
                "username": "charge1",
                "first_name": "Alain", "last_name": "Mbarga",
                "email": "charge1@maintenance.cm",
                "password": "Charge@1234",
                "role": "CHARGE_CONSIGNATION",
                "entite": dist,
            },
            {
                "username": "charge2",
                "first_name": "Samuel", "last_name": "Nkoa",
                "email": "charge2@maintenance.cm",
                "password": "Charge@1234",
                "role": "CHARGE_CONSIGNATION",
                "entite": trans,
            },
            # ── Chargés de consignation des plannings ──
            {"username": "abena.justin",      "first_name": "Justin",      "last_name": "ABENA",    "email": "abena.justin@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "abouna.christophe", "first_name": "Christophe",  "last_name": "ABOUNA",   "email": "abouna.christophe@maintenance.cm", "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "ateba.serge",       "first_name": "Serge",       "last_name": "ATEBA",    "email": "ateba.serge@maintenance.cm",       "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "beyala.francois",   "first_name": "François",    "last_name": "BEYALA",   "email": "beyala.francois@maintenance.cm",   "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "djomo.gustave",     "first_name": "Gustave",     "last_name": "DJOMO",    "email": "djomo.gustave@maintenance.cm",     "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "eboumbou.marcel",   "first_name": "Marcel",      "last_name": "EBOUMBOU", "email": "eboumbou.marcel@maintenance.cm",   "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "essomba.paul",      "first_name": "Paul",        "last_name": "ESSOMBA",  "email": "essomba.paul@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "eyinga.leopold",    "first_name": "Léopold",     "last_name": "EYINGA",   "email": "eyinga.leopold@maintenance.cm",    "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "fogue.henri",       "first_name": "Henri",       "last_name": "FOGUE",    "email": "fogue.henri@maintenance.cm",       "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "fouda.emmanuel",    "first_name": "Emmanuel",    "last_name": "FOUDA",    "email": "fouda.emmanuel@maintenance.cm",    "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "kollo.rene",        "first_name": "René",        "last_name": "KOLLO",    "email": "kollo.rene@maintenance.cm",        "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": trans},
            {"username": "mbarga.theodore",   "first_name": "Théodore",    "last_name": "MBARGA",   "email": "mbarga.theodore@maintenance.cm",   "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": trans},
            {"username": "mbia.jean-pierre",  "first_name": "Jean-Pierre", "last_name": "MBIA",     "email": "mbia.jean-pierre@maintenance.cm",  "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "mekongo.dieudonne", "first_name": "Dieudonné",   "last_name": "MEKONGO",  "email": "mekongo.dieudonne@maintenance.cm", "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "mvondo.andre",      "first_name": "André",       "last_name": "MVONDO",   "email": "mvondo.andre@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "ndjock.herman",     "first_name": "Herman",      "last_name": "NDJOCK",   "email": "ndjock.herman@maintenance.cm",     "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": trans},
            {"username": "ngamba.sylvestre",  "first_name": "Sylvestre",   "last_name": "NGAMBA",   "email": "ngamba.sylvestre@maintenance.cm",  "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "ngono.albert",      "first_name": "Albert",      "last_name": "NGONO",    "email": "ngono.albert@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "nkeng.robert",      "first_name": "Robert",      "last_name": "NKENG",    "email": "nkeng.robert@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "nkoa.patrick",      "first_name": "Patrick",     "last_name": "NKOA",     "email": "nkoa.patrick@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "nlend.gaston",      "first_name": "Gaston",      "last_name": "NLEND",    "email": "nlend.gaston@maintenance.cm",      "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "onana.clement",     "first_name": "Clément",     "last_name": "ONANA",    "email": "onana.clement@maintenance.cm",     "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "samba.theophile",   "first_name": "Théophile",   "last_name": "SAMBA",    "email": "samba.theophile@maintenance.cm",   "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
            {"username": "tamo.pierre",       "first_name": "Pierre",      "last_name": "TAMO",     "email": "tamo.pierre@maintenance.cm",       "password": "Charge@1234", "role": "CHARGE_CONSIGNATION", "entite": dist},
        ]

        for u in users_data:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    "first_name":   u['first_name'],
                    "last_name":    u['last_name'],
                    "email":        u['email'],
                    "is_superuser": u.get('is_superuser', False),
                    "is_staff":     u.get('is_staff', False),
                    "is_ldap":      False,
                    "first_connection": False,
                    "entite_metier": u.get('entite'),
                }
            )
            if created:
                user.set_password(u['password'])
                user.save()

            role = Role.objects.get(code_role=u['role'])
            UserRole.objects.get_or_create(user=user, role=role)

            statut = "créé ✅" if created else "existant ⏭️"
            self.stdout.write(f"  👤 {u['username']} ({u['role']}) → {statut}")

        self.stdout.write("✅ Utilisateurs créés")

    # ─────────────────────────────────────────
    # 6. RÉFÉRENTIEL
    # ─────────────────────────────────────────
    def _seed_referentiel(self):
        from referentiel.models import (
            TypeReferentiel, Reference, ReferentielItem, Centrale
        )
        from user.models import EntiteMetier

        prod  = EntiteMetier.objects.get(name="Production")
        trans = EntiteMetier.objects.get(name="Transport")
        dist  = EntiteMetier.objects.get(name="Distribution")

        # ── Types de référentiel ──
        types = ['SEGMENT', 'POSTE', 'OUVRAGE', 'DEPART', 'TRONCON']
        type_objs = {}
        for t in types:
            obj, _ = TypeReferentiel.objects.get_or_create(nom=t)
            type_objs[t] = obj
        self.stdout.write("  ✅ Types référentiel créés")

        # ── Centrales thermiques ──
        centrales = [
            "CENTRALE THERMIQUE LOGBABA GAZ",
            "CENTRALE THERMIQUE LOGBABA 2",
            "CENTRALE THERMIQUE OYOMABANG 1",
            "CENTRALE THERMIQUE OYOMABANG 2",
            "CENTRALE THERMIQUE BAFOUSSAM",
            "CENTRALE THERMIQUE BERTOUA",
            "CENTRALE THERMIQUE BAMENDA",
            "CENTRALE THERMIQUE MBALMAYO",
            "CENTRALE THERMIQUE EBOLOWA",
            "KPDC", "DPDC",
            "CENTRALE THERMIQUE LIMBE",
        ]
        for c in centrales:
            Centrale.objects.get_or_create(valeur=c)
        self.stdout.write("  ✅ Centrales créées")

        # ── Références avec leurs items ──
        references_data = [
            # DISTRIBUTION
            {
                "valeur": "DISTRIBUTION-DRY_BRGM_TRANSFO N°1 90/15kV_BRG.D11 P4",
                "entite": dist,
                "items": [
                    ("SEGMENT", "DISTRIBUTION-DRY"),
                    ("POSTE",   "BRGM"),
                    ("OUVRAGE", "TRANSFO N°1 90/15kV"),
                    ("DEPART",  "BRG.D11 P4"),
                ]
            },
            {
                "valeur": "DISTRIBUTION-DRY_BRGM_TRANSFO N°1 90/15kV_BRG.D12 MESSA",
                "entite": dist,
                "items": [
                    ("SEGMENT", "DISTRIBUTION-DRY"),
                    ("POSTE",   "BRGM"),
                    ("OUVRAGE", "TRANSFO N°1 90/15kV"),
                    ("DEPART",  "BRG.D12 MESSA"),
                ]
            },
            {
                "valeur": "DISTRIBUTION-DRY_AHALA_TRANSFO N°1 90/15kV_AHA.D11 OBAM ONGOLA",
                "entite": dist,
                "items": [
                    ("SEGMENT", "DISTRIBUTION-DRY"),
                    ("POSTE",   "AHALA"),
                    ("OUVRAGE", "TRANSFO N°1 90/15kV"),
                    ("DEPART",  "AHA.D11 OBAM ONGOLA"),
                ]
            },
            {
                "valeur": "DISTRIBUTION-DRD_KOUMASSI_TRANSFO N°1 90/15kV_KOU.D12 AKWA",
                "entite": dist,
                "items": [
                    ("SEGMENT", "DISTRIBUTION-DRD"),
                    ("POSTE",   "KOUMASSI"),
                    ("OUVRAGE", "TRANSFO N°1 90/15kV"),
                    ("DEPART",  "KOU.D12 AKWA"),
                ]
            },
            {
                "valeur": "DISTRIBUTION-DRD_BASSA_TRANSFO N°1 90/15kV_BAS.D11BASSA NORD",
                "entite": dist,
                "items": [
                    ("SEGMENT", "DISTRIBUTION-DRD"),
                    ("POSTE",   "BASSA"),
                    ("OUVRAGE", "TRANSFO N°1 90/15kV"),
                    ("DEPART",  "BAS.D11BASSA NORD"),
                ]
            },
            # TRANSPORT
            {
                "valeur": "TRANSPORT-CSE_BRGM_POSTE SOURCE_HTB_AT N°1 90/15kV",
                "entite": trans,
                "items": [
                    ("SEGMENT", "TRANSPORT-CSE"),
                    ("POSTE",   "BRGM"),
                    ("OUVRAGE", "POSTE SOURCE_HTB"),
                    ("DEPART",  "AT N°1 90/15kV"),
                ]
            },
            {
                "valeur": "TRANSPORT-CSE_BRGM_POSTE SOURCE_HTB_AT N°2 90/15kV",
                "entite": trans,
                "items": [
                    ("SEGMENT", "TRANSPORT-CSE"),
                    ("POSTE",   "BRGM"),
                    ("OUVRAGE", "POSTE SOURCE_HTB"),
                    ("DEPART",  "AT N°2 90/15kV"),
                ]
            },
            {
                "valeur": "TRANSPORT-LSO_KOUMASSI_POSTE SOURCE_HTB_AT N°1 90/15kV",
                "entite": trans,
                "items": [
                    ("SEGMENT", "TRANSPORT-LSO"),
                    ("POSTE",   "KOUMASSI"),
                    ("OUVRAGE", "POSTE SOURCE_HTB"),
                    ("DEPART",  "AT N°1 90/15kV"),
                ]
            },
            {
                "valeur": "TRANSPORT-LSO_BASSA_POSTE SOURCE_HTB_AT N°1 90/15kV",
                "entite": trans,
                "items": [
                    ("SEGMENT", "TRANSPORT-LSO"),
                    ("POSTE",   "BASSA"),
                    ("OUVRAGE", "POSTE SOURCE_HTB"),
                    ("DEPART",  "AT N°1 90/15kV"),
                ]
            },
            # PRODUCTION
            {
                "valeur": "PRODUCTION - EDEA_DCP_Groupe 01 - TR01",
                "entite": prod,
                "items": [
                    ("SEGMENT", "PRODUCTION - EDEA"),
                    ("OUVRAGE", "DCP"),
                    ("DEPART",  "Groupe 01 - TR01"),
                ]
            },
            {
                "valeur": "PRODUCTION - EDEA_DCP_Groupe 02 - TR02",
                "entite": prod,
                "items": [
                    ("SEGMENT", "PRODUCTION - EDEA"),
                    ("OUVRAGE", "DCP"),
                    ("DEPART",  "Groupe 02 - TR02"),
                ]
            },
            {
                "valeur": "PRODUCTION - LAGDO_DCP_Groupe 1 - TR01",
                "entite": prod,
                "items": [
                    ("SEGMENT", "PRODUCTION - LAGDO"),
                    ("OUVRAGE", "DCP"),
                    ("DEPART",  "Groupe 1 - TR01"),
                ]
            },
        ]

        for r in references_data:
            ref, _ = Reference.objects.get_or_create(
                valeur=r['valeur'],
                defaults={"entite_metier": r['entite']}
            )
            for type_nom, valeur in r['items']:
                ReferentielItem.objects.get_or_create(
                    reference=ref,
                    type=type_objs[type_nom],
                    defaults={"valeur": valeur}
                )

        self.stdout.write("✅ Référentiel créé")

    # ─────────────────────────────────────────
    # 7. TYPES D'ACTIVITÉ
    # ─────────────────────────────────────────
    def _seed_types_activite(self):
        from planning.models import TypeActivite
        from user.models import EntiteMetier

        prod  = EntiteMetier.objects.get(name="Production")
        trans = EntiteMetier.objects.get(name="Transport")
        dist  = EntiteMetier.objects.get(name="Distribution")

        types_data = [
            # PRODUCTION
            {"libelle": "CONTROLES GENERAUX",                    "entite": prod},
            {"libelle": "Révision ciblée",                       "entite": prod},
            {"libelle": "Entretien",                             "entite": prod},
            # TRANSPORT
            {"libelle": "Entretien appareillages de protection HTB", "entite": trans},
            {"libelle": "Entretien Jeu de barres",               "entite": trans},
            {"libelle": "Entretien transformateurs HTB",         "entite": trans},
            {"libelle": "Entretien lignes de transport",         "entite": trans},
            {"libelle": "Mise en service travée",                "entite": trans},
            {"libelle": "Entretien Auxiliaire de commande",      "entite": trans},
            # DISTRIBUTION
            {"libelle": "CONFECTION",                            "entite": dist},
            {"libelle": "CONSTRUCTION",                          "entite": dist},
            {"libelle": "CONTROLES GENERAUX DIST",               "entite": dist},
            {"libelle": "DEPLACEMENT",                           "entite": dist},
            {"libelle": "Elagage et Abattage",                   "entite": dist},
            {"libelle": "Entretien Diagnostic poste HTB/HTA",    "entite": dist},
            {"libelle": "INSPECTION",                            "entite": dist},
            {"libelle": "MAINTENANCE",                           "entite": dist},
            {"libelle": "Maintenance de réseau",                 "entite": dist},
            {"libelle": "Maintenance des poteaux bois",          "entite": dist},
            {"libelle": "Maintenance des transformateurs",       "entite": dist},
            {"libelle": "NORMALISATION",                         "entite": dist},
            {"libelle": "RACCORDEMENT",                          "entite": dist},
            {"libelle": "REHABILITATION",                        "entite": dist},
            {"libelle": "REMPLACEMENT",                          "entite": dist},
            {"libelle": "RENFORCEMENT",                          "entite": dist},
            {"libelle": "REPARATION",                            "entite": dist},
        ]

        for t in types_data:
            # ``libelle`` n'est pas unique en base. On scope la recherche à
            # l'entité et on prend le premier résultat si un ancien seed a
            # déjà créé des doublons.
            if not TypeActivite.objects.filter(
                libelle=t['libelle'], entite_metier=t['entite']
            ).exists():
                TypeActivite.objects.create(
                    libelle=t['libelle'], entite_metier=t['entite']
                )
        self.stdout.write("✅ Types d'activité créés")

    # ─────────────────────────────────────────
    # 8. WORKFLOW
    # ─────────────────────────────────────────
    def _seed_workflow(self):
        from pilotage.management.commands.seed_workflow import STEPS_DATA, TRANSITIONS_DATA
        from pilotage.models import (
            Workflow, WorkflowStep, WorkflowTransition, WorkflowValidation
        )
        from security.models import Role

        admin = User.objects.get(username='admin')

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

        # Nettoyage si le workflow existait déjà avec d'anciens steps
        if not wf_created:
            WorkflowTransition.objects.filter(workflow=workflow).delete()
            WorkflowStep.objects.filter(workflow=workflow).delete()

        # ── Steps ──
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

        # ── Transitions + Validations (rôles) ──
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
            if t["role_code"]:
                try:
                    role = Role.objects.get(code_role=t["role_code"])
                    WorkflowValidation.objects.create(
                        transition=transition,
                        role=role,
                        step=steps[t["from"]],
                    )
                except Role.DoesNotExist:
                    pass

        # Réparer les plannings orphelins (current_step mis à NULL par la
        # suppression/recréation des steps, FK on_delete=SET_NULL).
        from planning.models import Planning
        nb = Planning.objects.filter(
            workflow=workflow, current_step__isnull=True
        ).update(current_step=steps["CREER"])
        if nb:
            self.stdout.write(f"   {nb} planning(s) orphelin(s) reinitialise(s) a CREER")

        self.stdout.write("✅ Workflow créé (5 steps + 5 transitions)")

    # ─────────────────────────────────────────
    # 9. PLANNINGS ET TRAVAUX DE TEST
    # ─────────────────────────────────────────
    def _seed_plannings_et_travaux(self):
        from planning.models import Planning, Travail, TypeActivite
        from pilotage.models import Workflow, WorkflowStep
        from referentiel.models import Reference, Region
        from user.models import EntiteMetier, UniteDemanderesse

        operateur1 = User.objects.get(username='operateur1')
        operateur2 = User.objects.get(username='operateur2')
        charge1    = User.objects.get(username='charge1')
        charge2    = User.objects.get(username='charge2')

        dist  = EntiteMetier.objects.get(name="Distribution")
        trans = EntiteMetier.objects.get(name="Transport")
        prod  = EntiteMetier.objects.get(name="Production")

        workflow   = Workflow.objects.get(code="TRAVAUX_PROGRAMMES")
        step_init  = WorkflowStep.objects.get(workflow=workflow, code="CREER")

        unite_dist  = UniteDemanderesse.objects.filter(entite_metier=dist).first()
        unite_trans = UniteDemanderesse.objects.filter(entite_metier=trans).first()
        unite_prod  = UniteDemanderesse.objects.filter(entite_metier=prod).first()

        def _type_activite(libelle, entite=None):
            qs = TypeActivite.objects.filter(libelle=libelle)
            if entite is not None:
                type_entite = qs.filter(entite_metier=entite).first()
                if type_entite:
                    return type_entite
            return qs.first()

        type_maintenance  = _type_activite("MAINTENANCE", dist)
        type_remplacement = _type_activite("REMPLACEMENT", dist)
        type_inspection   = _type_activite("INSPECTION", dist)
        type_entretien    = _type_activite("Entretien", trans)

        ref_dist1 = Reference.objects.filter(valeur__startswith="DISTRIBUTION-DRY_BRGM_TRANSFO N°1 90/15kV_BRG.D11").first()
        ref_dist2 = Reference.objects.filter(valeur__startswith="DISTRIBUTION-DRY_BRGM_TRANSFO N°1 90/15kV_BRG.D12").first()
        ref_trans = Reference.objects.filter(valeur__startswith="TRANSPORT-CSE_BRGM_POSTE SOURCE_HTB_AT N°1").first()
        ref_prod  = Reference.objects.filter(valeur__startswith="PRODUCTION - EDEA_DCP_Groupe 01").first()

        # Région de test nécessaire pour que _partage_ressource puisse comparer les régions
        region_brgm, _ = Region.objects.get_or_create(code='BRGM')
        for ref in [ref_dist1, ref_dist2, ref_trans]:
            if ref and ref.region is None:
                ref.region = region_brgm
                ref.save()

        # get_or_create tolérant aux doublons : la base peut déjà contenir
        # plusieurs plannings du même nom (imports répétés), ce qui ferait
        # planter un get_or_create classique (MultipleObjectsReturned).
        def _planning(nom, defaults):
            p = Planning.objects.filter(nom=nom).first()
            if p:
                return p, False
            return Planning.objects.create(nom=nom, **defaults), True

        # ── Planning DISTRIBUTION ──
        planning_dist, _ = _planning(
            nom="Planning Distribution Juillet 2026",
            defaults={
                "entite_metier": dist,
                "workflow": workflow,
                "current_step": step_init,
                "cree_par": operateur1,
                "modifie_par": operateur1,
            }
        )

        # Travaux DISTRIBUTION avec chevauchement intentionnel pour tester l'alignement
        travaux_dist = [
            {
                "segment": "DISTRIBUTION",
                "priorite": "P2",
                "reference": ref_dist1,
                "type_travaux": type_maintenance,
                "unite_demanderesse": unite_dist,
                "consistance_travaux": "Maintenance préventive transformateur BRGM",
                "heure_debut_planifie": timezone.make_aware(
                    timezone.datetime(2026, 7, 19, 8, 0)
                ),
                "duree": 4, "unite_duree": "HEURES",
                "date_programmee": timezone.datetime(2026, 7, 14).date(),
                "charge_consignation": charge1,
                "type_reseau": "HTA",
            },
            {
                "segment": "DISTRIBUTION",
                "priorite": "P3",
                "reference": ref_dist1,  # même référence → chevauchement !
                "type_travaux": type_inspection,
                "unite_demanderesse": unite_dist,
                "consistance_travaux": "Inspection câbles BRGM",
                "heure_debut_planifie": timezone.make_aware(
                    timezone.datetime(2026, 7, 19, 10, 0)  # chevauchement avec le 1er
                ),
                "duree": 3, "unite_duree": "HEURES",
                "date_programmee": timezone.datetime(2026, 7, 14).date(),
                "charge_consignation": charge1,
                "type_reseau": "HTA",
            },
            {
                "segment": "DISTRIBUTION",
                "priorite": "P3",
                "reference": ref_dist2,
                "type_travaux": type_remplacement,
                "unite_demanderesse": unite_dist,
                "consistance_travaux": "Remplacement fusibles BRGM MESSA",
                "heure_debut_planifie": timezone.make_aware(
                    timezone.datetime(2026, 7, 19, 9, 0)
                ),
                "duree": 2, "unite_duree": "HEURES",
                "date_programmee": timezone.datetime(2026, 7, 14).date(),
                "charge_consignation": charge1,
                "type_reseau": "HTA",
            },
        ]

        for t in travaux_dist:
            Travail.objects.get_or_create(
                planning=planning_dist,
                reference=t['reference'],
                heure_debut_planifie=t['heure_debut_planifie'],
                defaults={
                    "segment": t['segment'],
                    "priorite": t['priorite'],
                    "type_travaux": t['type_travaux'],
                    "unite_demanderesse": t.get('unite_demanderesse'),
                    "consistance_travaux": t['consistance_travaux'],
                    "duree": t['duree'],
                    "unite_duree": t['unite_duree'],
                    "date_programmee": t['date_programmee'],
                    "charge_consignation": t.get('charge_consignation'),
                    "type_reseau": t.get('type_reseau'),
                    "niveau_coupure": "POSTE",
                    "entite_metier": dist,
                    "cree_par": operateur1,
                    "modifie_par": operateur1,
                }
            )

        # ── Planning TRANSPORT ──
        planning_trans, _ = _planning(
            nom="Planning Transport Juillet 2026",
            defaults={
                "entite_metier": trans,
                "workflow": workflow,
                "current_step": step_init,
                "cree_par": operateur2,
                "modifie_par": operateur2,
            }
        )

        Travail.objects.get_or_create(
            planning=planning_trans,
            reference=ref_trans,
            heure_debut_planifie=timezone.make_aware(
                timezone.datetime(2026, 7, 19, 8, 0)
            ),
            defaults={
                "segment": "TRANSPORT",
                "priorite": "P1",
                "type_travaux": type_entretien,
                "unite_demanderesse": unite_trans,
                "consistance_travaux": "Entretien autotransformateur BRGM HTB",
                "duree": 8, "unite_duree": "HEURES",
                "date_programmee": timezone.datetime(2026, 7, 14).date(),
                "charge_consignation": charge2,
                "entite_metier": trans,
                "cree_par": operateur2,
                "modifie_par": operateur2,
            }
        )

        # ── Planning PRODUCTION ──
        planning_prod, _ = _planning(
            nom="Planning Production Juillet 2026",
            defaults={
                "entite_metier": prod,
                "workflow": workflow,
                "current_step": step_init,
                "cree_par": operateur1,
                "modifie_par": operateur1,
            }
        )

        centrale = __import__(
            'referentiel.models', fromlist=['Centrale']
        ).Centrale.objects.filter(valeur__icontains="EDEA").first()

        Travail.objects.get_or_create(
            planning=planning_prod,
            reference=ref_prod,
            heure_debut_planifie=timezone.make_aware(
                timezone.datetime(2026, 7, 20, 6, 0)
            ),
            defaults={
                "segment": "PRODUCTION",
                "priorite": "P2",
                "type_travaux": _type_activite("Révision ciblée", prod),
                "unite_demanderesse": unite_prod,
                "consistance_travaux": "Révision groupe 01 centrale EDEA",
                "duree": 6, "unite_duree": "HEURES",
                "date_programmee": timezone.datetime(2026, 7, 15).date(),
                "disponibilite_mecanique_mw": 120.00,
                "prevision_puissance_sollicitee": 100.00,
                "prevision_puissance_interrompue": 20.00,
                "centrale_thermique_sollicitee": centrale,
                "entite_metier": prod,
                "cree_par": operateur1,
                "modifie_par": operateur1,
            }
        )

        self.stdout.write("✅ Plannings et travaux de test créés")
        self.stdout.write(f"  📋 Planning Distribution : {planning_dist.code}")
        self.stdout.write(f"  📋 Planning Transport    : {planning_trans.code}")
        self.stdout.write(f"  📋 Planning Production   : {planning_prod.code}")

    # ─────────────────────────────────────────────────────────────────────────
    # 10. SCÉNARIOS D'HARMONISATION POSTE → RAME → LIGNE
    # ─────────────────────────────────────────────────────────────────────────
    def _seed_scenarios_harmonisation(self):
        """Crée des jeux de données démontrant la hiérarchie électrique.

        Les items ``POSTE``, ``RAME`` et ``DEPART`` sont volontairement
        renseignés sur les références. C'est cette structure, et non le texte
        de la référence, qui est utilisée par l'algorithme d'harmonisation.
        """
        from datetime import datetime

        from planning.models import Planning, Travail, TypeActivite, PropositionAlignement
        from pilotage.models import Workflow, WorkflowStep
        from referentiel.models import Reference, ReferentielItem, Region, TypeReferentiel
        from user.models import EntiteMetier, UniteDemanderesse

        distribution = EntiteMetier.objects.get(name="Distribution")
        operateur = User.objects.get(username='operateur1')
        charge = User.objects.get(username='charge1')
        charge_pivot = User.objects.get(username='charge2')
        workflow = Workflow.objects.get(code="TRAVAUX_PROGRAMMES")
        step_initial = WorkflowStep.objects.get(workflow=workflow, code="CREER")
        unite = UniteDemanderesse.objects.filter(entite_metier=distribution).first()
        maintenance = TypeActivite.objects.filter(
            libelle="MAINTENANCE", entite_metier=distribution
        ).first()
        inspection = TypeActivite.objects.filter(
            libelle="INSPECTION", entite_metier=distribution
        ).first()
        region, _ = Region.objects.get_or_create(code='BRGM')

        type_items = {
            nom: TypeReferentiel.objects.get_or_create(nom=nom)[0]
            for nom in ('SEGMENT', 'POSTE', 'RAME', 'DEPART', 'OUVRAGE')
        }

        def reference(valeur, items):
            ref, _ = Reference.objects.get_or_create(
                valeur=valeur,
                defaults={'entite_metier': distribution, 'region': region},
            )
            # Les références peuvent avoir été créées auparavant : on complète
            # alors leur région et leurs items sans écraser d'autres données.
            if ref.region_id is None:
                ref.region = region
                ref.save(update_fields=['region'])
            for type_nom, valeur_item in items:
                ReferentielItem.objects.get_or_create(
                    reference=ref,
                    type=type_items[type_nom],
                    valeur=valeur_item,
                )
            return ref

        poste = 'BRGM_POSTE SOURCE_HTA'
        rame_1 = 'RAME 15kV N°1'
        rame_2 = 'RAME 15kV N°2'
        commun_poste = [('SEGMENT', 'DISTRIBUTION-MAINTENANCE POSTES'), ('POSTE', poste)]

        ref_poste = reference(
            'DEMO_HARMONISATION_BRGM_POSTE_SOURCE_HTA',
            commun_poste + [('OUVRAGE', 'POSTE SOURCE HTA')],
        )
        ref_rame_1 = reference(
            'DEMO_HARMONISATION_BRGM_TRANSFO_1_RAME_1',
            commun_poste + [('OUVRAGE', 'TRANSFO 90/15kV N°1'), ('RAME', rame_1)],
        )
        ref_ligne_1 = reference(
            'DEMO_HARMONISATION_BRGM_RAME_1_BRG_D11',
            commun_poste + [('OUVRAGE', 'TRANSFO 90/15kV N°1'), ('RAME', rame_1), ('DEPART', 'BRG.D11 P4')],
        )
        ref_ligne_2 = reference(
            'DEMO_HARMONISATION_BRGM_RAME_1_BRG_D12',
            commun_poste + [('OUVRAGE', 'TRANSFO 90/15kV N°1'), ('RAME', rame_1), ('DEPART', 'BRG.D12 MESSA')],
        )
        ref_ligne_rame_2 = reference(
            'DEMO_HARMONISATION_BRGM_RAME_2_BRG_D17',
            commun_poste + [('OUVRAGE', 'TRANSFO 90/15kV N°2'), ('RAME', rame_2), ('DEPART', 'BRG.D17 PALAIS DES CONGRES')],
        )

        def planning(nom):
            plan, _ = Planning.objects.get_or_create(
                nom=nom,
                defaults={
                    'entite_metier': distribution, 'workflow': workflow,
                    'current_step': step_initial, 'cree_par': operateur,
                    'modifie_par': operateur,
                },
            )
            return plan

        def moment(jour, heure):
            return timezone.make_aware(datetime(2026, 8, jour, heure, 0))

        def travail(plan, ref, debut, duree, coupure, priorite, libelle,
                    aligne=False, charge_consignation=None):
            obj, _ = Travail.objects.get_or_create(
                planning=plan, reference=ref, heure_debut_planifie=debut,
                defaults={
                    'segment': 'DISTRIBUTION', 'priorite': priorite,
                    'type_travaux': maintenance if priorite == 'P2' else inspection,
                    'unite_demanderesse': unite, 'consistance_travaux': libelle,
                    'duree': duree, 'unite_duree': 'HEURES',
                    'date_programmee': debut.date(),
                    'charge_consignation': charge_consignation or charge,
                    'type_reseau': 'HTA', 'niveau_coupure': coupure,
                    'entite_metier': distribution, 'travail_en_alignement': aligne,
                    'cree_par': operateur, 'modifie_par': operateur,
                },
            )
            if aligne and not obj.travail_en_alignement:
                obj.travail_en_alignement = True
                obj.modifie_par = operateur
                obj.save(update_fields=['travail_en_alignement', 'modifie_par', 'date_modification'])
            return obj

        # Cas 1 : une coupure au poste source doit proposer d'aligner une ligne
        # de la rame 1 et une ligne de la rame 2 (toutes deux sous ce poste).
        a_harmoniser = planning('DEMO - Harmonisation BRGM à traiter (août 2026)')
        travail(a_harmoniser, ref_poste, moment(18, 8), 8, 'POSTES', 'P2',
                'Maintenance au poste source BRGM : impacte toutes les rames',
                charge_consignation=charge_pivot)
        travail(a_harmoniser, ref_ligne_1, moment(18, 10), 3, 'DEPARTS', 'P3',
                'Inspection ligne BRG.D11 : proposition attendue sur le poste source')
        travail(a_harmoniser, ref_ligne_rame_2, moment(18, 11), 2, 'DEPARTS', 'P3',
                'Inspection ligne BRG.D17 : proposition attendue sur le poste source')

        # Cas 2 : une coupure de rame n'impacte que les lignes de cette rame.
        travail(a_harmoniser, ref_rame_1, moment(20, 8), 6, 'RAME', 'P2',
                'Maintenance de la rame 1 : impacte uniquement ses départs',
                charge_consignation=charge_pivot)
        travail(a_harmoniser, ref_ligne_2, moment(20, 10), 2, 'DEPARTS', 'P3',
                'Inspection ligne BRG.D12 : proposition attendue sur la rame 1')

        # Cas 3 : travaux déjà alignés ; le marqueur et la proposition acceptée
        # permettent de les identifier directement dans le calendrier.
        deja_harmonise = planning('DEMO - Harmonisation BRGM déjà réalisée (août 2026)')
        pivot = travail(deja_harmonise, ref_poste, moment(25, 8), 6, 'POSTES', 'P2',
                         'Coupure poste source BRGM déjà coordonnée', aligne=True)
        cible = travail(deja_harmonise, ref_ligne_1, moment(25, 8), 3, 'DEPARTS', 'P3',
                         'Ligne BRG.D11 déjà alignée sur la coupure poste', aligne=True)
        PropositionAlignement.objects.get_or_create(
            planning=deja_harmonise,
            travail_a_modifier=cible,
            travail_reference=pivot,
            defaults={
                'type_proposition': PropositionAlignement.TypeProposition.ALIGNEMENT_TRAVAUX,
                'type_travaux_reference': maintenance.libelle,
                'type_travaux_a_modifier': inspection.libelle,
                'priorite_travail': cible.priorite,
                'ancien_debut': moment(25, 10), 'ancienne_fin': moment(25, 13),
                'nouveau_debut': cible.heure_debut_planifie,
                'nouvelle_fin': cible.heure_fin_planifie,
                'raison': 'Démo : la ligne BRG.D11 a été alignée sur la coupure du poste source BRGM.',
                'statut': PropositionAlignement.Statut.ACCEPTEE,
                'cree_par': operateur,
            },
        )

        self.stdout.write('✅ Scénarios démonstratifs d’harmonisation BRGM créés (août 2026)')

    # ─────────────────────────────────────────
    # RÉCAPITULATIF
    # ─────────────────────────────────────────
    def _print_recap(self):
        self.stdout.write(self.style.SUCCESS('\n📋 COMPTES DE TEST :'))
        self.stdout.write('  admin          / Admin@1234        → Accès total')
        self.stdout.write('  operateur1     / Operateur@1234    → Crée les travaux DISTRIBUTION')
        self.stdout.write('  operateur2     / Operateur@1234    → Crée les travaux TRANSPORT')
        self.stdout.write('  gestionnaire1  / Gestionnaire@1234 → Analyse et aligne')
        self.stdout.write('  responsable1   / Responsable@1234  → Valide et génère DDR')
        self.stdout.write('  ccr1           / Ccr@1234          → Décide sur les DDR')
        self.stdout.write('  charge1        / Charge@1234       → Charge consignation DIST')
        self.stdout.write('  charge2        / Charge@1234       → Charge consignation TRANS')
        self.stdout.write(self.style.SUCCESS('\n✅ Tout est prêt pour les tests !\n'))
