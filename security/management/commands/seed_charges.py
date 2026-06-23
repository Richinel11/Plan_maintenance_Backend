from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


CHARGES_DISTRIBUTION = [
    ("ABENA",     "Justin"),
    ("ABOUNA",    "Christophe"),
    ("DJOMO",     "Gustave"),
    ("EBOUMBOU",  "Marcel"),
    ("EYINGA",    "Léopold"),
    ("FOGUE",     "Henri"),
    ("KOLLO",     "René"),
    ("MEKONGO",   "Dieudonné"),
    ("NGAMBA",    "Sylvestre"),
    ("NKOA",      "Patrick"),
    ("SAMBA",     "Théophile"),
    ("TAMO",      "Pierre"),
]

CHARGES_TRANSPORT = [
    ("ATEBA",    "Serge"),
    ("BEYALA",   "François"),
    ("ESSOMBA",  "Paul"),
    ("FOUDA",    "Emmanuel"),
    ("MBARGA",   "Théodore"),
    ("MBIA",     "Jean-Pierre"),
    ("MVONDO",   "André"),
    ("NDJOCK",   "Herman"),
    ("NGONO",    "Albert"),
    ("NKENG",    "Robert"),
    ("NLEND",    "Gaston"),
    ("ONANA",    "Clément"),
]


def _username(nom, prenom):
    import unicodedata
    def strip_accents(s):
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )
    nom_clean    = strip_accents(nom.lower()).replace('-', '_').replace(' ', '_')
    prenom_clean = strip_accents(prenom.lower()).replace('-', '_').replace(' ', '_')
    return f"{prenom_clean}_{nom_clean}"


class Command(BaseCommand):
    help = 'Crée les chargés de consignation issus des plannings Excel réels'

    def handle(self, *args, **kwargs):
        self._creer_charges()
        self._creer_region_et_assigner()
        self._corriger_niveau_coupure()
        self._print_recap()

    # ──────────────────────────────────────────────────────────────
    # 1. CHARGÉS DE CONSIGNATION
    # ──────────────────────────────────────────────────────────────
    def _creer_charges(self):
        from security.models import Role, UserRole
        from user.models import EntiteMetier

        role = Role.objects.get(code_role='CHARGE_CONSIGNATION')
        dist = EntiteMetier.objects.get(name='Distribution')
        trans = EntiteMetier.objects.get(name='Transport')

        total_crees = 0

        for entite, liste in [(dist, CHARGES_DISTRIBUTION), (trans, CHARGES_TRANSPORT)]:
            for nom, prenom in liste:
                username = _username(nom, prenom)
                email = f"{username}@maintenance.cm"

                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name':       prenom,
                        'last_name':        nom,
                        'email':            email,
                        'entite_metier':    entite,
                        'is_ldap':          False,
                        'first_connection': False,
                    }
                )

                if created:
                    user.set_password('Charge@1234')
                    user.save()
                    total_crees += 1

                UserRole.objects.get_or_create(user=user, role=role)

                statut = '✅ créé' if created else '⏭️  existe'
                self.stdout.write(f"  {statut} — {prenom} {nom} ({entite.name})")

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Chargés de consignation : {total_crees} créé(s), '
            f'{len(CHARGES_DISTRIBUTION) + len(CHARGES_TRANSPORT) - total_crees} déjà existant(s)'
        ))

    # ──────────────────────────────────────────────────────────────
    # 2. RÉGION + AFFECTATION AUX RÉFÉRENCES
    # ──────────────────────────────────────────────────────────────
    def _creer_region_et_assigner(self):
        from referentiel.models import Region, Reference

        region, created = Region.objects.get_or_create(code='SUD')
        statut = 'créée' if created else 'déjà existante'
        self.stdout.write(f'\n✅ Région SUD {statut}')

        # Assigner à toutes les références qui n'ont pas encore de région
        refs_sans_region = Reference.objects.filter(region__isnull=True)
        nb = refs_sans_region.update(region=region)
        self.stdout.write(f'✅ {nb} référence(s) assignée(s) à la région SUD')

    # ──────────────────────────────────────────────────────────────
    # 3. NIVEAU COUPURE SUR LES TRAVAUX DISTRIBUTION EXISTANTS
    # ──────────────────────────────────────────────────────────────
    def _corriger_niveau_coupure(self):
        from planning.models import Travail

        nb = Travail.objects.filter(
            segment='DISTRIBUTION',
            niveau_coupure__isnull=True,
        ).update(niveau_coupure='POSTE')

        self.stdout.write(
            f'✅ {nb} travail(x) DISTRIBUTION mis à jour → niveau_coupure=POSTE'
        )

    # ──────────────────────────────────────────────────────────────
    # RÉCAPITULATIF
    # ──────────────────────────────────────────────────────────────
    def _print_recap(self):
        self.stdout.write(self.style.SUCCESS('\n📋 COMPTES CHARGÉS DE CONSIGNATION :'))
        self.stdout.write('  Mot de passe commun : Charge@1234')
        self.stdout.write('\n  DISTRIBUTION :')
        for nom, prenom in CHARGES_DISTRIBUTION:
            self.stdout.write(f'    {_username(nom, prenom):<30} → {prenom} {nom}')
        self.stdout.write('\n  TRANSPORT :')
        for nom, prenom in CHARGES_TRANSPORT:
            self.stdout.write(f'    {_username(nom, prenom):<30} → {prenom} {nom}')
        self.stdout.write(self.style.SUCCESS(
            '\n✅ Lance maintenant : POST /plannings/{id}/analyser-chevauchements/'
        ))
