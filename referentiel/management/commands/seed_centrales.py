import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
EXCEL_PATH = os.path.join(BASE_DIR, "docs", "BD asset - système électrique (1) (1).xlsx")
SHEET_NAME = "Centrale thermique sollicitée"


class Command(BaseCommand):
    help = "Seed Centrale depuis la feuille « Centrale thermique sollicitée » du fichier Excel"

    def handle(self, *args, **kwargs):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write("openpyxl manquant — lancez : pip install openpyxl")
            return

        from referentiel.models import Centrale

        wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
        ws = wb[SHEET_NAME]

        created_count = 0
        skipped_count = 0

        for row in ws.rows:
            for cell in row:
                val = str(cell.value).strip() if cell.value else None
                if not val:
                    continue

                _, created = Centrale.objects.get_or_create(
                    nom=val,
                    defaults={"actif": True},
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  [+] {val}")
                else:
                    skipped_count += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed Centrale terminé : "
            f"{created_count} créées, {skipped_count} déjà existantes."
        ))
