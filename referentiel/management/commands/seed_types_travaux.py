import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
EXCEL_PATH = os.path.join(BASE_DIR, "docs", "BD asset - système électrique (1) (1).xlsx")
SHEET_NAME = "Type de travaux"

# col_index → EntiteMetier name
COL_MAP = {
    2: "Production",
    3: "Transport",
    4: "Distribution",
}


class Command(BaseCommand):
    help = "Seed TypeActivite depuis la feuille « Type de travaux » du fichier Excel"

    def handle(self, *args, **kwargs):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write("openpyxl manquant — lancez : pip install openpyxl")
            return

        from planning.models import TypeActivite
        from user.models import EntiteMetier

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
        rows = list(ws.rows)[1:]  # skip header

        created_count = 0
        skipped_count = 0

        for row in rows:
            for col_idx, entite_name in COL_MAP.items():
                cell = row[col_idx] if col_idx < len(row) else None
                val = str(cell.value).strip() if cell and cell.value else None
                if not val:
                    continue

                entite = entites[entite_name]
                _, created = TypeActivite.objects.get_or_create(
                    libelle=val,
                    entite_metier=entite,
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  [+] {val}  →  {entite_name}")
                else:
                    skipped_count += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed TypeActivite terminé : "
            f"{created_count} créés, {skipped_count} déjà existants."
        ))
