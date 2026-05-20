import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
EXCEL_PATH = os.path.join(BASE_DIR, "docs", "BD asset - système électrique (1) (1).xlsx")

SHEET_CONFIG = {
    "Type réseau et Réf production": "Production",
    "Type de réseau et réf transport": "Transport",
    "Type de réseau et réf distribut": "Distribution",
}


class Command(BaseCommand):
    help = "Seed referentiel depuis le fichier Excel BD asset"

    def handle(self, *args, **kwargs):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write("openpyxl manquant — lancez: pip install openpyxl")
            return

        from referentiel.models import Ouvrage, Poste, Depart, Troncon
        from user.models import EntiteMetier

        # Charger les 3 entités — elles doivent exister (seed_entite_metier)
        try:
            entites = {e.name: e for e in EntiteMetier.objects.filter(
                name__in=["Production", "Transport", "Distribution"]
            )}
            assert len(entites) == 3
        except (AssertionError, Exception):
            self.stderr.write(
                "Les 3 EntiteMetier (Production, Transport, Distribution) sont introuvables.\n"
                "Lancez d'abord : python manage.py seed_entite_metier"
            )
            return

        wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

        stats = {"troncon": 0, "ouvrage": 0, "poste": 0, "depart": 0}

        for sheet_name, entite_name in SHEET_CONFIG.items():
            entite = entites[entite_name]
            ws = wb[sheet_name]
            rows = [r for r in list(ws.rows)[2:] if any(c.value for c in r)]
            self.stdout.write(f"\n→ {sheet_name} ({len(rows)} lignes) → {entite_name}")

            for row in rows:
                vals = [c.value for c in row]
                col0 = str(vals[0]).strip() if vals[0] else None
                col1 = str(vals[1]).strip() if len(vals) > 1 and vals[1] else None
                col2 = str(vals[2]).strip() if len(vals) > 2 and vals[2] else None
                col3 = str(vals[3]).strip() if len(vals) > 3 and vals[3] else None

                if not col0 or col0.startswith("=") or col0 == "Segment":
                    continue

                # Troncon — col 1 pour tous les segments
                if col1 and not col1.startswith("="):
                    _, created = Troncon.objects.get_or_create(
                        nom=col1,
                        entite_metier=entite,
                        defaults={"actif": True},
                    )
                    if created:
                        stats["troncon"] += 1

                if entite_name == "Distribution":
                    # Poste — col 2
                    if col2 and not col2.startswith("="):
                        _, created = Poste.objects.get_or_create(
                            nom=col2,
                            entite_metier=entite,
                            defaults={"actif": True},
                        )
                        if created:
                            stats["poste"] += 1
                    # Depart — col 3
                    if col3 and not col3.startswith("="):
                        _, created = Depart.objects.get_or_create(
                            nom=col3,
                            entite_metier=entite,
                            defaults={"actif": True},
                        )
                        if created:
                            stats["depart"] += 1
                else:
                    # Ouvrage — col 2 pour PROD et TRANSPORT
                    if col2 and not col2.startswith("="):
                        _, created = Ouvrage.objects.get_or_create(
                            nom=col2,
                            entite_metier=entite,
                            defaults={"type": col1 or ""},
                        )
                        if created:
                            stats["ouvrage"] += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed terminé :"
            f"\n  Troncon : {stats['troncon']}"
            f"\n  Ouvrage : {stats['ouvrage']}"
            f"\n  Poste   : {stats['poste']}"
            f"\n  Depart  : {stats['depart']}"
        ))
