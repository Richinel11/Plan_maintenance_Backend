import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
EXCEL_PATH = os.path.join(BASE_DIR, "docs", "BD asset - système électrique (1) (1).xlsx")

# Structure réelle du fichier Excel (vérifiée ligne d'en-tête) :
#   col 0 : "Segment"      → TypeReferentiel "Segment"
#   col 1 : "OUVRAGES..."  → TypeReferentiel "Ouvrage"
#   col 2 : "GR/TFO/..."   → TypeReferentiel "Poste"
#   col 3 : "DEPARTS"      → TypeReferentiel "Départ"  (distribution uniquement)
#
# Chaque colonne produit un ReferentielItem. La valeur de la Reference
# est la concaténation de toutes les valeurs non vides (ordre de col_map).
#
# sheet name → (entite_metier_name, [(col_index, TypeReferentiel.nom), ...])
SHEET_CONFIG = {
    "Type réseau et Réf production": ("Production", [
        (0, "Segment"),
        (1, "Ouvrage"),
        (2, "Poste"),
    ]),
    "Type de réseau et réf transport": ("Transport", [
        (0, "Segment"),
        (1, "Ouvrage"),
        (2, "Poste"),
    ]),
    "Type de réseau et réf distribut": ("Distribution", [
        (0, "Segment"),
        (1, "Ouvrage"),
        (2, "Poste"),
        (3, "Départ"),
    ]),
}

TYPE_NOMS = ["Segment", "Ouvrage", "Poste", "Départ"]


class Command(BaseCommand):
    help = "Seed TypeReferentiel, Reference et ReferentielItem depuis le fichier Excel BD asset"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help="Supprime tous les TypeReferentiel, Reference et ReferentielItem avant de re-seeder",
        )

    def handle(self, *args, **kwargs):
        try:
            import openpyxl
        except ImportError:
            self.stderr.write("openpyxl manquant — lancez : pip install openpyxl")
            return

        from referentiel.models import TypeReferentiel, Reference, ReferentielItem
        from user.models import EntiteMetier

        # ── Reset optionnel ───────────────────────────────────────────────────
        if kwargs['reset']:
            deleted_items, _ = ReferentielItem.objects.all().delete()
            deleted_refs, _ = Reference.objects.all().delete()
            deleted_types, _ = TypeReferentiel.objects.all().delete()
            self.stdout.write(
                f"  [reset] {deleted_types} TypeReferentiel, "
                f"{deleted_refs} Reference, "
                f"{deleted_items} ReferentielItem supprimés"
            )

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

            # Ligne 0 = titre éventuel, ligne 1 = en-têtes → on commence à la ligne 2
            rows = [r for r in list(ws.rows)[2:] if any(c.value for c in r)]
            self.stdout.write(f"\n  → {sheet_name} [{entite_name}] ({len(rows)} lignes)")

            for row in rows:
                vals = [c.value for c in row]

                # Lire toutes les colonnes définies dans col_map (col 0 inclus)
                col_vals = {}
                for col_idx, type_nom in col_map:
                    raw = vals[col_idx] if col_idx < len(vals) else None
                    val = str(raw).strip() if raw and str(raw).strip() and not str(raw).startswith("=") else None
                    col_vals[type_nom] = val

                # Ignorer la ligne d'en-tête résiduelle et les lignes vides
                segment = col_vals.get("Segment")
                if not segment or segment == "Segment" or not any(col_vals.values()):
                    continue

                # Valeur de la référence : toutes les valeurs non vides dans l'ordre
                parts = [v for v in col_vals.values() if v]
                ref_valeur = "_".join(parts)

                # Étape 2 : Reference
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
