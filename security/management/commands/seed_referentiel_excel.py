import re
import openpyxl
from django.core.management.base import BaseCommand
from referentiel.models import TypeReferentiel, Reference, ReferentielItem
from user.models import EntiteMetier
     
REGIONS_VALIDES = [
    'DRY', 'DRC', 'DRSANO', 'DRSOM', 'DRE', 'DRONO', 'DRSM', 'DRNEA', 'DRD'
]

# Table d'alias — corrige les incohérences de nommage entre feuilles Excel.
# À enrichir au fur et à mesure que le client signale de nouveaux cas.
ALIAS_POSTE = {
    'NYOM II': 'NYOM',
    'MILE 2 LIMBE': 'MILE2 LIMBE',
}


def normaliser_poste(poste: str) -> str:
    return ALIAS_POSTE.get(poste, poste)


def extraire_poste(segment: str, ouvrage: str) -> str:
    if segment.startswith('PRODUCTION'):
        parts = segment.split(' - ')
        poste = parts[-1].strip() if len(parts) > 1 else segment.strip()
        return normaliser_poste(poste)

    match = re.match(r'^([^_]+(?:\s[^_]+)*?)(?:_POSTE SOURCE|_LIGNE|$)', ouvrage.strip())
    poste = match.group(1).strip() if match else ouvrage.split('_')[0].strip()
    return normaliser_poste(poste)


def extraire_type_poste(segment: str, ouvrage: str) -> str:
    ouvrage_upper = ouvrage.upper()
    # "POSTE SOURCE" classique OU "POSTE DE XXX" (cas MANGOMBE)
    if 'POSTE SOURCE' in ouvrage_upper or re.search(r'POSTE DE \w+', ouvrage_upper):
        return 'POSTE_SOURCE'
    if 'LIGNE' in ouvrage_upper:
        return 'LIGNE'
    if segment.startswith('PRODUCTION'):
        return 'PRODUCTION'
    return 'DEPART'


def extraire_region(segment: str) -> str | None:
    if not segment.startswith('DISTRIBUTION-'):
        return None
    code = segment.replace('DISTRIBUTION-', '').strip()
    return code if code in REGIONS_VALIDES else None


class Command(BaseCommand):
    help = 'Génère le référentiel (Reference + ReferentielItem) depuis le fichier Excel BD_asset'

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str)

    def handle(self, *args, **options):
        wb = openpyxl.load_workbook(options['excel_path'], data_only=True)

        # Types référentiel
        types = {}
        for nom in ['SEGMENT', 'POSTE', 'TYPE_POSTE', 'REGION', 'OUVRAGE', 'DEPART']:
            types[nom], _ = TypeReferentiel.objects.get_or_create(nom=nom)

        entites = {
            'PRODUCTION': EntiteMetier.objects.get(type='PROD'),
            'TRANSPORT': EntiteMetier.objects.get(type='TRANS'),
            'DISTRIBUTION': EntiteMetier.objects.get(type='DIST'),
        }

        sheets_config = [
            ('Type réseau et Réf production', 'PRODUCTION', 3),
            ('Type de réseau et réf transport', 'TRANSPORT', 4),
            ('Type de réseau et réf distribut', 'DISTRIBUTION', 5),
        ]

        # PASSE 1 : poste → région (déduit des segments DISTRIBUTION-DR*)
        poste_region = {}
        ws_dist = wb['Type de réseau et réf distribut']
        for row in ws_dist.iter_rows(min_row=3, values_only=True):
            if not row[0]:
                continue
            segment = str(row[0]).strip()
            ouvrage = str(row[1]).strip() if row[1] else ''
            region = extraire_region(segment)
            if region:
                poste_region[extraire_poste(segment, ouvrage)] = region

        # PASSE 2 : créer Reference + ReferentielItem
        total = 0
        sans_region = set()

        for sheet_name, entite_key, ref_col_index in sheets_config:
            ws = wb[sheet_name]
            for row in ws.iter_rows(min_row=3, values_only=True):
                if not row[0]:
                    continue

                segment = str(row[0]).strip()
                ouvrage = str(row[1]).strip() if row[1] else ''
                gr_tfo = str(row[2]).strip() if row[2] else ''
                depart = str(row[3]).strip() if entite_key == 'DISTRIBUTION' and row[3] else None
                reference_val = str(row[ref_col_index - 1]).strip() if row[ref_col_index - 1] else ''

                if not reference_val or reference_val == 'None':
                    continue

                poste = extraire_poste(segment, ouvrage)
                type_poste = extraire_type_poste(segment, ouvrage)
                region = poste_region.get(poste)

                if not region:
                    sans_region.add((poste, entite_key))

                ref, _ = Reference.objects.get_or_create(
                    valeur=reference_val,
                    defaults={"entite_metier": entites[entite_key]}
                )

                items_to_create = [
                    ('SEGMENT', segment),
                    ('POSTE', poste),
                    ('TYPE_POSTE', type_poste),
                ]
                if region:
                    items_to_create.append(('REGION', region))
                if gr_tfo:
                    items_to_create.append(('OUVRAGE', gr_tfo))
                if depart:
                    items_to_create.append(('DEPART', depart))

                for type_nom, valeur in items_to_create:
                    ReferentielItem.objects.get_or_create(
                        reference=ref, type=types[type_nom],
                        defaults={"valeur": valeur}
                    )
                total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {total} références traitées"))
        if sans_region:
            self.stdout.write(self.style.WARNING(
                f"⚠️  {len(sans_region)} poste(s) sans région (à clarifier avec le client) :"
            ))
            for poste, entite in sorted(sans_region):
                self.stdout.write(f"     - {poste} ({entite})")