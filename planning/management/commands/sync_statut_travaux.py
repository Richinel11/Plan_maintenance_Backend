"""
Rattrapage ponctuel de ``Travail.statut_travaux``.

Le champ n'a jamais été avancé par l'application (les actions soumettre() /
valider() de planning.views ne sont appelées par aucun écran), si bien que des
travaux dont la NAPT est diffusée depuis longtemps sont restés BROUILLON. La
synchronisation est désormais automatique via les signaux DDR/NAPT ; cette
commande rattrape le stock existant.

    python manage.py sync_statut_travaux --dry-run   # visualiser
    python manage.py sync_statut_travaux             # appliquer

Sorties volontairement en ASCII : la console Windows (cp1252) n'affiche pas
les emojis.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from exploitation.services import (
    statut_travail_attendu,
    synchroniser_statut_travail,
)
from planning.models import Travail


class Command(BaseCommand):
    help = (
        "Aligne statut_travaux sur l'avancement DDR/NAPT des travaux existants "
        "(DDR generee -> SOUMIS, NAPT diffusee -> VALIDE)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="N'ecrit rien : affiche seulement ce qui serait modifie.",
        )

    def _repartition(self, titre):
        self.stdout.write("")
        self.stdout.write("Repartition statut_travaux (%s) :" % titre)
        lignes = (Travail.objects
                  .values('statut_travaux')
                  .annotate(n=Count('id'))
                  .order_by('-n'))
        for ligne in lignes:
            self.stdout.write("   %-12s %d" % (ligne['statut_travaux'], ligne['n']))

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self._repartition("AVANT")

        travaux = (Travail.objects
                   .select_related('demande_retrait', 'note_arret', 'reference')
                   .order_by('date_creation'))

        a_modifier = []
        for travail in travaux:
            cible = statut_travail_attendu(travail)
            if cible is not None:
                a_modifier.append((travail, travail.statut_travaux, cible))

        self.stdout.write("")
        if not a_modifier:
            self.stdout.write("Aucun travail a mettre a jour.")
            return

        self.stdout.write("%d travail(aux) a mettre a jour :" % len(a_modifier))
        for travail, actuel, cible in a_modifier:
            reference = travail.reference.valeur if travail.reference else '(sans reference)'
            self.stdout.write(
                "   %-38s %-10s -> %s" % (reference[:38], actuel, cible)
            )

        if dry_run:
            self.stdout.write("")
            self.stdout.write("--dry-run : aucune ecriture effectuee.")
            return

        modifies = sum(1 for travail, _, _ in a_modifier
                       if synchroniser_statut_travail(travail))

        self.stdout.write("")
        self.stdout.write("%d travail(aux) mis a jour." % modifies)
        self._repartition("APRES")
