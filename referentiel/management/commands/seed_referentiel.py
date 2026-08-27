import json
import os
from django.core.management.base import BaseCommand

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
DATA_DIR = os.path.join(BASE_DIR, "referentiel", "data")

# Fichiers source (copies de feat/*.json) → entité métier associée.
JSON_FILES = {
    "distribution_posts.json": "Distribution",
    "transport.json": "Transport",
    "production.json": "Production",
}

TYPE_NOMS = ["Segment", "Ouvrage", "Poste", "Départ"]

# Règles de remplissage :
#
# - Reference : valeur = son champ `reference` ; entite_metier = celle du
#   fichier ; region = Region liée au champ `region` de l'entrée si fourni,
#   sinon None ; date_creation automatique.
#
# - ReferentielItem, un par type Segment/Ouvrage/Poste/Départ, uniquement
#   quand une valeur existe :
#     - distribution_posts.json (structure imbriquée posts[] → lignes[]) :
#         * une entrée posts[i] ("type post") reçoit Segment = segment du
#           GROUPE parent (pas son propre champ `segment`), Ouvrage = la clé
#           top-level du groupe (pas son propre champ `ouvrage`),
#           Poste = son propre `gr_tfo_postes`. Pas de Départ.
#         * une entrée lignes[j] ("type ligne") reçoit Segment/Ouvrage/Départ
#           = ses propres champs, Poste = hérité du `gr_tfo_postes` du
#           posts[i] parent (les lignes n'ont pas ce champ).
#     - transport.json / production.json (structure plate, pas de champ
#       region/depart/ouvrage par entrée) : chaque entrée reçoit
#       Segment = segment du groupe, Ouvrage = clé top-level du groupe,
#       Poste = son propre `gr_tfo_postes`. Pas de Départ (aucune valeur
#       distincte disponible dans ces fichiers), pas de région.


class Command(BaseCommand):
    help = "Seed TypeReferentiel, Reference et ReferentielItem depuis les fichiers JSON de referentiel/data/"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help="Supprime tous les TypeReferentiel, Reference et ReferentielItem avant de re-seeder",
        )

    def handle(self, *args, **kwargs):
        from referentiel.models import TypeReferentiel, Reference, ReferentielItem, Region
        from user.models import EntiteMetier

        # ── Reset optionnel ───────────────────────────────────────────────
        if kwargs['reset']:
            deleted_items, _ = ReferentielItem.objects.all().delete()
            deleted_refs, _ = Reference.objects.all().delete()
            deleted_types, _ = TypeReferentiel.objects.all().delete()
            self.stdout.write(
                f"  [reset] {deleted_types} TypeReferentiel, "
                f"{deleted_refs} Reference, "
                f"{deleted_items} ReferentielItem supprimés"
            )

        # ── Vérifier les EntiteMetier ────────────────────────────────────
        entites = {e.name: e for e in EntiteMetier.objects.filter(
            name__in=["Production", "Transport", "Distribution"]
        )}
        if len(entites) < 3:
            self.stderr.write(
                "Les 3 EntiteMetier sont introuvables. "
                "Lancez d'abord : python manage.py seed_all (ou seed_entite_metier)"
            )
            return

        # ── TypeReferentiel ──────────────────────────────────────────────
        self.stdout.write("\n[1/3] TypeReferentiel...")
        types = {}
        for nom in TYPE_NOMS:
            obj, created = TypeReferentiel.objects.get_or_create(nom=nom)
            types[nom] = obj
            self.stdout.write(f"  {'[+]' if created else '[ ]'} {nom}")

        # ── Helpers ──────────────────────────────────────────────────────
        region_cache = {}

        def get_region(code):
            if not code:
                return None
            if code not in region_cache:
                region_cache[code] = Region.objects.get_or_create(code=code)[0]
            return region_cache[code]

        stats = {"reference": 0, "item": 0}

        def creer_reference(valeur, entite, region_code, items):
            """Crée une Reference (region=None si non fournie) + ses
            ReferentielItem (un par (type, valeur) fourni, ignoré si valeur
            vide/absente)."""
            reference, created = Reference.objects.get_or_create(
                valeur=valeur,
                defaults={"entite_metier": entite, "region": get_region(region_code)},
            )
            if created:
                stats["reference"] += 1
            for type_nom, item_valeur in items:
                if not item_valeur:
                    continue
                _, item_created = ReferentielItem.objects.get_or_create(
                    reference=reference, type=types[type_nom],
                    defaults={"valeur": item_valeur},
                )
                if item_created:
                    stats["item"] += 1
            return reference

        def charger(nom_fichier):
            with open(os.path.join(DATA_DIR, nom_fichier), encoding='utf-8') as f:
                return json.load(f)

        # ── [2/3] + [3/3] Reference + ReferentielItem ───────────────────
        self.stdout.write("\n[2/3] Reference  +  [3/3] ReferentielItem...")

        # DISTRIBUTION — structure imbriquée posts[] → lignes[]
        entite = entites["Distribution"]
        for poste_key, groupe in charger("distribution_posts.json").items():
            segment_groupe = groupe.get('segment')
            for post in groupe.get('posts', []):
                gr_tfo = post.get('gr_tfo_postes')
                creer_reference(
                    post['reference'], entite, post.get('region'),
                    [
                        ('Segment', segment_groupe),
                        ('Ouvrage', poste_key),
                        ('Poste', gr_tfo),
                    ],
                )
                for ligne in post.get('lignes', []):
                    creer_reference(
                        ligne['reference'], entite, ligne.get('region'),
                        [
                            ('Segment', ligne.get('segment')),
                            ('Ouvrage', ligne.get('ouvrage')),
                            ('Poste', gr_tfo),
                            ('Départ', ligne.get('depart')),
                        ],
                    )
        self.stdout.write(f"  → distribution_posts.json [Distribution]")

        # TRANSPORT / PRODUCTION — structure plate (posts[] uniquement)
        for nom_fichier, entite_name in JSON_FILES.items():
            if nom_fichier == "distribution_posts.json":
                continue
            entite = entites[entite_name]
            for groupe_key, groupe in charger(nom_fichier).items():
                segment_groupe = groupe.get('segment')
                for post in groupe.get('posts', []):
                    creer_reference(
                        post['reference'], entite, None,
                        [
                            ('Segment', segment_groupe),
                            ('Ouvrage', groupe_key),
                            ('Poste', post.get('gr_tfo_postes')),
                        ],
                    )
            self.stdout.write(f"  → {nom_fichier} [{entite_name}]")

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed terminé :"
            f"\n  Reference      : {stats['reference']}"
            f"\n  ReferentielItem: {stats['item']}"
        ))
