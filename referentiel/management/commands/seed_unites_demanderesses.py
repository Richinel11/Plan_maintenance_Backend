import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
EXCEL_PATH = os.path.join(BASE_DIR, "docs", "BD asset - système électrique (1) (1).xlsx")
SHEET_NAME = "Unité demanderesse"

ENTITE_MAP = {
    "PRODUCTION":   "Production",
    "TRANSPORT":    "Transport",
    "DISTRIBUTION": "Distribution",
}


class Command(BaseCommand):
    help = "Seed UniteDemanderesse depuis la feuille « Unité demanderesse » du fichier Excel"

    def handle(self, *args, **kwargs):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write("openpyxl manquant — lancez : pip install openpyxl")
            return

        from user.models import EntiteMetier, UniteDemanderesse

        # Charger les 3 EntiteMetier
        entites = {e.name: e for e in EntiteMetier.objects.filter(
            name__in=["Production", "Transport", "Distribution"]
        )}
        if len(entites) < 3:
            self.stderr.write(
                "Les 3 EntiteMetier sont introuvables. "
                "Lancez d'abord : python manage.py seed_entite_metier"
            )
            return

        wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
        ws = wb[SHEET_NAME]

        current_entite = None
        created_count = 0
        skipped_count = 0

        for row in ws.rows:
            col0 = str(row[0].value).strip() if row[0].value else None
            col1 = str(row[1].value).strip() if len(row) > 1 and row[1].value else None

            if col0 and col0.upper() in ENTITE_MAP:
                current_entite = entites[ENTITE_MAP[col0.upper()]]

            if col1 and current_entite:
                _, created = UniteDemanderesse.objects.get_or_create(
                    nom=col1,
                    entite_metier=current_entite,
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  [+] {col1}  →  {current_entite.name}")
                else:
                    skipped_count += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed UniteDemanderesse terminé : "
            f"{created_count} créées, {skipped_count} déjà existantes."
        ))
