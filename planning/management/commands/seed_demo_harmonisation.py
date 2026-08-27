# planning/management/commands/seed_demo_harmonisation.py
#
# Six scénarios de démonstration du module d'harmonisation des plannings,
# un par mois (septembre 2026 → février 2027), pensés pour être présentés
# en changeant simplement le mois sur la page Alertes : chaque mois ne
# contient QUE le cas qu'il illustre, rien d'autre.
#
#   - Septembre 2026 : alignement TRANSPORT ↔ DISTRIBUTION (cas phare).
#   - Octobre 2026   : groupe transitif à 3 travaux (union-find) + les deux
#                      niveaux de note de compatibilité (OPTIMAL/ATTENTION).
#   - Novembre 2026  : travail P1 non déplaçable → proposition BLOQUEE.
#   - Décembre 2026  : conflit de charge de consignation avec un travail
#                      tiers déjà en base → proposition BLOQUEE.
#   - Janvier 2027   : deux travaux du même groupe partageant le même
#                      chargé de consignation → un seul passe EN_ATTENTE,
#                      l'autre BLOQUEE (protection ajoutée le 2026-08-23,
#                      voir alignement_service._charge_disponible /
#                      analyser_mois.alignements_proposes).
#   - Février 2027   : alignement verrouillé manuellement par un
#                      gestionnaire (Travail.alignement_verrouille) — reste
#                      BLOQUEE avec un motif dédié même sous un pivot
#                      TRANSPORT.
#
# Prérequis : `python manage.py seed_all` (entités, utilisateurs, types
# d'activité, workflow) doit avoir été lancé au moins une fois avant.
#
# Idempotent : peut être relancé sans dupliquer les données (clé :
# planning + reference + heure_debut_planifie pour les travaux).

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed de 6 scénarios de démonstration de l'harmonisation, un par mois"

    def handle(self, *args, **kwargs):
        from planning.models import Planning, Travail, TypeActivite
        from pilotage.models import Workflow, WorkflowStep
        from referentiel.models import Reference, ReferentielItem, Region, TypeReferentiel
        from user.models import EntiteMetier, UniteDemanderesse

        distribution = EntiteMetier.objects.get(name="Distribution")
        transport = EntiteMetier.objects.get(name="Transport")
        operateur_dist = User.objects.get(username='operateur1')
        operateur_trans = User.objects.get(username='operateur2')
        charge_dist = User.objects.get(username='charge1')
        charge_trans = User.objects.get(username='charge2')
        charge_dist_bis = User.objects.get(username='mbia.jean-pierre')
        workflow = Workflow.objects.get(code="TRAVAUX_PROGRAMMES")
        step_initial = WorkflowStep.objects.get(workflow=workflow, code="EN_ATTENTE")
        unite_dist = UniteDemanderesse.objects.filter(entite_metier=distribution).first()

        types_dist = {
            libelle: TypeActivite.objects.filter(libelle=libelle, entite_metier=distribution).first()
            for libelle in ('MAINTENANCE', 'INSPECTION', 'REMPLACEMENT', 'CONSTRUCTION', 'NORMALISATION')
        }
        type_trans = TypeActivite.objects.filter(
            libelle="Entretien transformateurs HTB", entite_metier=transport
        ).first()

        type_items = {
            nom: TypeReferentiel.objects.get_or_create(nom=nom)[0]
            for nom in ('SEGMENT', 'POSTE', 'RAME', 'DEPART', 'OUVRAGE')
        }

        def region(code):
            return Region.objects.get_or_create(code=code)[0]

        def reference(valeur, entite, region_obj, items):
            ref, _ = Reference.objects.get_or_create(
                valeur=valeur,
                defaults={'entite_metier': entite, 'region': region_obj},
            )
            if ref.region_id is None:
                ref.region = region_obj
                ref.save(update_fields=['region'])
            for type_nom, valeur_item in items:
                ReferentielItem.objects.get_or_create(
                    reference=ref, type=type_items[type_nom], valeur=valeur_item,
                )
            return ref

        def planning(nom, entite):
            plan, _ = Planning.objects.get_or_create(
                nom=nom,
                defaults={
                    'entite_metier': entite, 'workflow': workflow,
                    'current_step': step_initial,
                    'cree_par': operateur_dist, 'modifie_par': operateur_dist,
                },
            )
            return plan

        def moment(annee, mois, jour, heure):
            return timezone.make_aware(datetime(annee, mois, jour, heure, 0))

        def travail(plan, ref, segment, debut, duree, coupure, priorite, type_activite,
                    libelle, charge_consignation, entite, operateur=None,
                    verrouille=False, type_reseau='HTA'):
            op = operateur or (operateur_trans if segment == 'TRANSPORT' else operateur_dist)
            obj, cree = Travail.objects.get_or_create(
                planning=plan, reference=ref, heure_debut_planifie=debut,
                defaults={
                    'segment': segment, 'priorite': priorite,
                    'type_travaux': type_activite,
                    'unite_demanderesse': unite_dist if segment != 'TRANSPORT' else None,
                    'consistance_travaux': libelle,
                    'duree': duree, 'unite_duree': 'HEURES',
                    'date_programmee': debut.date(),
                    'charge_consignation': charge_consignation,
                    'type_reseau': type_reseau, 'niveau_coupure': coupure,
                    'entite_metier': entite,
                    'alignement_verrouille': verrouille,
                    'cree_par': op, 'modifie_par': op,
                },
            )
            if not cree and obj.alignement_verrouille != verrouille:
                obj.alignement_verrouille = verrouille
                obj.save(update_fields=['alignement_verrouille'])
            return obj

        # ═══════════════════════════════════════════════════════════════
        # SEPTEMBRE 2026 — Cas phare : TRANSPORT ↔ DISTRIBUTION
        # ═══════════════════════════════════════════════════════════════
        r = region('NKG')
        plan_sept = planning('DEMO 09/2026 — Alignement Transport ↔ Distribution', transport)
        commun = [('SEGMENT', 'TRANSPORT-MAINTENANCE POSTES'), ('POSTE', 'TRANSFO 90/15kV NKONGSAMBA')]
        ref_transport = reference(
            'DEMO_SEPT_NKONGSAMBA_POSTE_SOURCE', transport, r,
            commun + [('OUVRAGE', 'POSTE SOURCE NKONGSAMBA')],
        )
        ref_dist = reference(
            'DEMO_SEPT_NKONGSAMBA_RAME1_D11', distribution, r,
            [('SEGMENT', 'DISTRIBUTION-MAINTENANCE RESEAU'), ('POSTE', 'TRANSFO 90/15kV NKONGSAMBA')]
            + [('OUVRAGE', 'POSTE SOURCE NKONGSAMBA'), ('RAME', 'RAME 15kV N°1'), ('DEPART', 'NKG.D11')],
        )
        travail(plan_sept, ref_transport, 'TRANSPORT', moment(2026, 9, 8, 8), 10, 'POSTES',
                None, type_trans, "Entretien transformateur 90/15kV : coupure du poste source",
                charge_trans, transport, type_reseau='HTB')
        travail(plan_sept, ref_dist, 'DISTRIBUTION', moment(2026, 9, 8, 14), 6, 'DEPARTS',
                'P3', types_dist['REMPLACEMENT'], "Remplacement isolateurs départ NKG.D11",
                charge_dist, distribution)

        # ═══════════════════════════════════════════════════════════════
        # OCTOBRE 2026 — Groupe transitif (union-find) + notes de compatibilité
        # ═══════════════════════════════════════════════════════════════
        r = region('EDA')
        plan_oct = planning('DEMO 10/2026 — Groupe transitif A-B-C', distribution)
        commun = [('SEGMENT', 'DISTRIBUTION-MAINTENANCE RESEAU'), ('POSTE', 'TRANSFO EDEA N°3'),
                  ('OUVRAGE', 'POSTE SOURCE EDEA'), ('RAME', 'RAME 15kV N°1')]
        ref_a = reference('DEMO_OCT_EDEA_D21', distribution, r, commun + [('DEPART', 'EDA.D21')])
        ref_b = reference('DEMO_OCT_EDEA_RAME1', distribution, r, commun)  # coupure rame entière
        ref_c = reference('DEMO_OCT_EDEA_D23', distribution, r, commun + [('DEPART', 'EDA.D23')])
        # B (P2) devient le pivot du groupe : sa priorité lui donne le score le
        # plus bas (contrairement à A et C, tous deux P3) — le choix du pivot
        # ne dépend pas de l'ordre de création ci-dessous.
        travail(plan_oct, ref_b, 'DISTRIBUTION', moment(2026, 10, 6, 9), 6, 'RAME',
                'P2', types_dist['REMPLACEMENT'], "Maintenance rame 1 (pivot du groupe)",
                charge_trans, distribution)
        travail(plan_oct, ref_a, 'DISTRIBUTION', moment(2026, 10, 6, 8), 3, 'DEPARTS',
                'P3', types_dist['REMPLACEMENT'],
                "Remplacement départ EDA.D21 : même type que le pivot → ATTENTION attendue",
                charge_dist, distribution)
        travail(plan_oct, ref_c, 'DISTRIBUTION', moment(2026, 10, 6, 13), 3, 'DEPARTS',
                'P3', types_dist['INSPECTION'],
                "Inspection départ EDA.D23 : léger + pivot lourd → OPTIMAL attendu",
                charge_dist_bis, distribution)

        # ═══════════════════════════════════════════════════════════════
        # NOVEMBRE 2026 — Travail P1 non déplaçable → BLOQUEE
        # ═══════════════════════════════════════════════════════════════
        # Le pivot doit être TRANSPORT (ou verrouillé) : face à un P2, un P1
        # reste toujours PLUS prioritaire (_score_priorite) et deviendrait
        # lui-même le pivot — ce qui masquerait complètement la démonstration
        # (le travail "P2 Maintenance poste" serait alors le déplaçable, pas
        # le P1). Seul TRANSPORT/verrouillé passe systématiquement devant P1.
        r = region('GRA')
        plan_nov = planning('DEMO 11/2026 — Travail P1 non déplaçable', transport)
        commun_t = [('SEGMENT', 'TRANSPORT-MAINTENANCE POSTES'), ('POSTE', 'TRANSFO GAROUA N°1')]
        ref_pivot = reference(
            'DEMO_NOV_GAROUA_POSTE_SOURCE', transport, r,
            commun_t + [('OUVRAGE', 'POSTE SOURCE GAROUA')],
        )
        ref_p1 = reference(
            'DEMO_NOV_GAROUA_D31', distribution, r,
            [('SEGMENT', 'DISTRIBUTION-MAINTENANCE RESEAU'), ('POSTE', 'TRANSFO GAROUA N°1')]
            + [('OUVRAGE', 'POSTE SOURCE GAROUA'), ('DEPART', 'GRA.D31')],
        )
        travail(plan_nov, ref_pivot, 'TRANSPORT', moment(2026, 11, 10, 8), 8, 'POSTES',
                None, type_trans, "Entretien transformateur 90/15kV : coupure du poste source",
                charge_trans, transport, type_reseau='HTB')
        travail(plan_nov, ref_p1, 'DISTRIBUTION', moment(2026, 11, 10, 10), 4, 'DEPARTS',
                'P1', types_dist['REMPLACEMENT'],
                "Dépannage urgent départ GRA.D31 (P1) : ne peut pas être déplacé",
                charge_dist, distribution)

        # ═══════════════════════════════════════════════════════════════
        # DÉCEMBRE 2026 — Conflit de charge de consignation (tiers déjà occupé)
        # ═══════════════════════════════════════════════════════════════
        r = region('BFM')
        plan_dec = planning('DEMO 12/2026 — Conflit de charge de consignation', distribution)
        commun = [('SEGMENT', 'DISTRIBUTION-MAINTENANCE POSTES'), ('POSTE', 'TRANSFO BAFOUSSAM N°1'),
                  ('OUVRAGE', 'POSTE SOURCE BAFOUSSAM')]
        ref_pivot = reference('DEMO_DEC_BAFOUSSAM_POSTE', distribution, r, commun)
        ref_cible = reference('DEMO_DEC_BAFOUSSAM_D41', distribution, r, commun + [('DEPART', 'BFM.D41')])
        # Référence sans aucun lien de ressource avec le groupe ci-dessus :
        # sert uniquement à occuper charge_dist sur le créneau visé par la
        # proposition (08h-10h), pour déclencher le conflit de charge.
        ref_tiers = reference(
            'DEMO_DEC_BAFOUSSAM_TIERS', distribution, r,
            [('SEGMENT', 'DISTRIBUTION-MAINTENANCE RESEAU'), ('POSTE', 'AUTRE POSTE SANS LIEN')],
        )
        travail(plan_dec, ref_pivot, 'DISTRIBUTION', moment(2026, 12, 8, 8), 10, 'POSTES',
                'P2', types_dist['MAINTENANCE'], "Maintenance poste source Bafoussam",
                charge_trans, distribution)
        travail(plan_dec, ref_cible, 'DISTRIBUTION', moment(2026, 12, 8, 9), 2, 'DEPARTS',
                'P3', types_dist['INSPECTION'],
                "Inspection départ BFM.D41 : chargé déjà occupé sur le créneau proposé (08h-10h)",
                charge_dist, distribution)
        travail(plan_dec, ref_tiers, 'DISTRIBUTION', moment(2026, 12, 8, 8) + timedelta(minutes=30), 1, 'DEPARTS',
                'P3', types_dist['INSPECTION'], "Travail sans lien, même chargé : occupe 08h30-09h30",
                charge_dist, distribution)

        # ═══════════════════════════════════════════════════════════════
        # JANVIER 2027 — Même chargé partagé entre 2 travaux du même groupe
        # ═══════════════════════════════════════════════════════════════
        r = region('MRA')
        plan_janv = planning('DEMO 01/2027 — Chargé partagé dans le même groupe', distribution)
        commun = [('SEGMENT', 'DISTRIBUTION-MAINTENANCE POSTES'), ('POSTE', 'TRANSFO MAROUA N°1'),
                  ('OUVRAGE', 'POSTE SOURCE MAROUA')]
        ref_pivot = reference('DEMO_JANV_MAROUA_POSTE', distribution, r, commun)
        ref_x = reference('DEMO_JANV_MAROUA_D51', distribution, r, commun + [('DEPART', 'MRA.D51')])
        ref_y = reference('DEMO_JANV_MAROUA_D52', distribution, r, commun + [('DEPART', 'MRA.D52')])
        travail(plan_janv, ref_pivot, 'DISTRIBUTION', moment(2027, 1, 12, 8), 12, 'POSTES',
                'P2', types_dist['MAINTENANCE'], "Maintenance poste source Maroua",
                charge_trans, distribution)
        # Les deux travaux ci-dessous partagent charge_dist. Tous deux se
        # voient proposer le MÊME début (08h, celui du pivot) une fois
        # calés — l'un des deux ressortira EN_ATTENTE, l'autre BLOQUEE pour
        # conflit de charge "dans cette même analyse" (alignements_proposes).
        # Lequel des deux dépend de l'ordre de traitement (date_creation) :
        # peu importe pour la démo, le point à montrer est qu'il y en a
        # toujours un des deux qui bloque, plus aucun des deux ne passe
        # silencieusement EN_ATTENTE.
        travail(plan_janv, ref_x, 'DISTRIBUTION', moment(2027, 1, 12, 12), 3, 'DEPARTS',
                'P3', types_dist['REMPLACEMENT'], "Départ MRA.D51 : partage le chargé du départ MRA.D52",
                charge_dist, distribution)
        travail(plan_janv, ref_y, 'DISTRIBUTION', moment(2027, 1, 12, 13), 2, 'DEPARTS',
                'P3', types_dist['INSPECTION'], "Départ MRA.D52 : partage le chargé du départ MRA.D51",
                charge_dist, distribution)

        # ═══════════════════════════════════════════════════════════════
        # FÉVRIER 2027 — Alignement verrouillé manuellement par un gestionnaire
        # ═══════════════════════════════════════════════════════════════
        r = region('LBE')
        plan_fev = planning('DEMO 02/2027 — Alignement verrouillé', transport)
        commun_t = [('SEGMENT', 'TRANSPORT-MAINTENANCE POSTES'), ('POSTE', 'TRANSFO LIMBE N°1')]
        ref_transport = reference(
            'DEMO_FEV_LIMBE_POSTE_SOURCE', transport, r,
            commun_t + [('OUVRAGE', 'POSTE SOURCE LIMBE')],
        )
        commun_d = [('SEGMENT', 'DISTRIBUTION-MAINTENANCE RESEAU'), ('POSTE', 'TRANSFO LIMBE N°1'),
                    ('OUVRAGE', 'POSTE SOURCE LIMBE')]
        ref_verrouille = reference('DEMO_FEV_LIMBE_D61', distribution, r, commun_d + [('DEPART', 'LBE.D61')])
        ref_mobile = reference('DEMO_FEV_LIMBE_D62', distribution, r, commun_d + [('DEPART', 'LBE.D62')])
        travail(plan_fev, ref_transport, 'TRANSPORT', moment(2027, 2, 9, 8), 10, 'POSTES',
                None, type_trans, "Entretien transformateur 90/15kV : coupure du poste source",
                charge_trans, transport, type_reseau='HTB')
        # Verrouillé manuellement : même si le TRANSPORT reste pivot (priorité
        # absolue), ce travail ne bougera plus JAMAIS et le motif de blocage
        # affiché doit être "alignement fixé manuellement", pas "P1"/"TRANSPORT".
        travail(plan_fev, ref_verrouille, 'DISTRIBUTION', moment(2027, 2, 9, 10), 4, 'DEPARTS',
                'P3', types_dist['CONSTRUCTION'],
                "Départ LBE.D61 : alignement déjà fixé manuellement par le gestionnaire",
                charge_dist, distribution, verrouille=True)
        travail(plan_fev, ref_mobile, 'DISTRIBUTION', moment(2027, 2, 9, 12), 4, 'DEPARTS',
                'P3', types_dist['INSPECTION'],
                "Départ LBE.D62 : déplaçable normalement, doit s'aligner sur le TRANSPORT",
                charge_dist_bis, distribution)

        self.stdout.write(self.style.SUCCESS(
            '✅ 6 scénarios de démonstration créés (septembre 2026 → février 2027)'
        ))
        self.stdout.write('  09/2026 → Transport ↔ Distribution')
        self.stdout.write('  10/2026 → Groupe transitif A-B-C + notes OPTIMAL/ATTENTION')
        self.stdout.write('  11/2026 → Travail P1 non déplaçable (BLOQUEE)')
        self.stdout.write('  12/2026 → Conflit de charge de consignation (BLOQUEE)')
        self.stdout.write('  01/2027 → Charge partagée dans le même groupe (BLOQUEE)')
        self.stdout.write('  02/2027 → Alignement verrouillé manuellement (BLOQUEE)')
