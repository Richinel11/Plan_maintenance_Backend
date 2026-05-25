import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
EXCEL_PATH = os.path.join(BASE_DIR, "docs", "BD asset - système électrique (1) (1).xlsx")

# sheet name → (entite_metier_name, ordered list of (col_index, TypeReferentiel.nom))
SHEET_CONFIG = {
    "Type réseau et Réf production": ("Production", [
        (1, "Tronçon"),
        (2, "Ouvrage"),
    ]),
    "Type de réseau et réf transport": ("Transport", [
        (1, "Tronçon"),
        (2, "Ouvrage"),
    ]),
    "Type de réseau et réf distribut": ("Distribution", [
        (1, "Tronçon"),
        (2, "Poste"),
        (3, "Départ"),
    ]),
}

TYPE_NOMS = ["Tronçon", "Ouvrage", "Poste", "Départ"]


class Command(BaseCommand):
    help = "Seed TypeReferentiel, Reference et ReferentielItem depuis le fichier Excel BD asset"

    def handle(self, *args, **kwargs):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write("openpyxl manquant — lancez : pip install openpyxl")
            return

        from referentiel.models import TypeReferentiel, Reference, ReferentielItem
        from user.models import EntiteMetier

        # ── Vérifier les EntiteMetier ─────────────────────────────────────────
        entites = {e.name: e for e in EntiteMetier.objects.filter(
            name__in=["Production", "Transport", "Distribution"]
        )}
        if len(entites) < 3:
            self.stderr.write(
                "Les 3 EntiteMetier sont introuvables. "
                "Lancez d'abord : python manage.py seed_entite_metier"
            )
            return

        # ── Étape 1 : TypeReferentiel ─────────────────────────────────────────
        self.stdout.write("\n[1/3] TypeReferentiel...")
        types = {}
        for nom in TYPE_NOMS:
            obj, created = TypeReferentiel.objects.get_or_create(nom=nom)
            types[nom] = obj
            self.stdout.write(f"  {'[+]' if created else '[ ]'} {nom}")

        # ── Étape 2 & 3 : Reference + ReferentielItem ─────────────────────────
        self.stdout.write("\n[2/3] Reference  +  [3/3] ReferentielItem...")

        wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

        stats = {"reference": 0, "item": 0}

        for sheet_name, (entite_name, col_map) in SHEET_CONFIG.items():
            entite = entites[entite_name]
            ws = wb[sheet_name]
            rows = [r for r in list(ws.rows)[2:] if any(c.value for c in r)]
            self.stdout.write(f"\n  → {sheet_name} [{entite_name}] ({len(rows)} lignes)")

            for row in rows:
                vals = [c.value for c in row]

                col0 = str(vals[0]).strip() if vals[0] else None
                if not col0 or col0.startswith("=") or col0 == "Segment":
                    continue

                # Collecter les valeurs des colonnes définies
                col_vals = {}
                for col_idx, type_nom in col_map:
                    raw = vals[col_idx] if col_idx < len(vals) else None
                    val = str(raw).strip() if raw and not str(raw).startswith("=") else None
                    col_vals[type_nom] = val

                if not any(col_vals.values()):
                    continue

                # Valeur de référence : col0 + valeurs dans l'ordre
                parts = [col0] + [v for v in col_vals.values() if v]
                ref_valeur = "_".join(parts)

                # Étape 2 : Reference (liée à l'entité métier)
                reference, created = Reference.objects.get_or_create(
                    valeur=ref_valeur,
                    entite_metier=entite,
                )
                if created:
                    stats["reference"] += 1

                # Étape 3 : ReferentielItem (un par colonne non vide)
                for type_nom, val in col_vals.items():
                    if not val:
                        continue
                    _, created = ReferentielItem.objects.get_or_create(
                        reference=reference,
                        type=types[type_nom],
                        defaults={"valeur": val},
                    )
                    if created:
                        stats["item"] += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed terminé :"
            f"\n  Reference      : {stats['reference']}"
            f"\n  ReferentielItem: {stats['item']}"
        ))
