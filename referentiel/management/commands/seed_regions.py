from django.core.management.base import BaseCommand
from referentiel.models import Region

REGION_CODES = [
    'DRD',
    'DRY',
    'DRC',
    'DRLSO',
    'DRONO',
    'DRN',
    'DRE',
    'DRS',
    'DRSO',
    # Codes du rapport "Suivi des travaux prévisionnels" (KPI direction)
    'CSE',
    'DRNEA',
    'DRSANO',
    'DRSOM',
    'EDEA',
    'LAGDO',
    'LSO',
    'ONO',
    'POSTE SOURCE',
    'SLL',
]


class Command(BaseCommand):
    help = "Seed les régions ENEO si elles n'existent pas"

    def handle(self, *args, **kwargs):
        created_count = 0
        skipped_count = 0

        for code in REGION_CODES:
            _, created = Region.objects.get_or_create(code=code)
            if created:
                created_count += 1
                self.stdout.write(f"  [+] {code}")
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed régions terminé : "
            f"{created_count} créées, {skipped_count} déjà existantes."
        ))
