# planning/management/commands/seed_kpi_avril_2026.py
#
# Jeu de données de démonstration pour Avril 2026, calibré pour peupler
# les 6 KPI de la page KPI (soutenance) : programmés / exécutés / non
# exécutés / harmonisés / par ouvrage / centrales IPP vs internes.
#
# Idempotent : peut être relancé sans dupliquer les travaux (clé :
# planning + reference/centrale + heure_debut_planifie).

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed de travaux Avril 2026 pour peupler les KPI de démonstration"

    def handle(self, *args, **kwargs):
        from planning.models import Planning, Travail, PropositionAlignement, TypeActivite
        from pilotage.models import Workflow, WorkflowStep
        from referentiel.models import Reference, Centrale
        from user.models import EntiteMetier, UniteDemanderesse

        operateur1 = User.objects.get(username='operateur1')
        operateur2 = User.objects.get(username='operateur2')
        charge1    = User.objects.get(username='charge1')
        charge2    = User.objects.get(username='charge2')

        dist  = EntiteMetier.objects.get(name="Distribution")
        trans = EntiteMetier.objects.get(name="Transport")
        prod  = EntiteMetier.objects.get(name="Production")

        workflow  = Workflow.objects.get(code="TRAVAUX_PROGRAMMES")
        step_init = WorkflowStep.objects.get(workflow=workflow, code="EN_ATTENTE")

        unite_dist  = UniteDemanderesse.objects.filter(entite_metier=dist).first()
        unite_trans = UniteDemanderesse.objects.filter(entite_metier=trans).first()

        unites_ipp = list(UniteDemanderesse.objects.filter(
            entite_metier=prod, nom__icontains='IPP'
        ))
        unites_interne = list(UniteDemanderesse.objects.filter(
            entite_metier=prod
        ).exclude(nom__icontains='IPP'))

        type_maintenance  = TypeActivite.objects.filter(libelle="MAINTENANCE").first()
        type_reparation    = TypeActivite.objects.filter(libelle="REPARATION").first()
        type_entretien_trans = TypeActivite.objects.filter(libelle="Entretien lignes de transport").first()
        type_entretien_prod  = TypeActivite.objects.filter(libelle="Entretien").first()

        def _planning(nom, entite, cree_par):
            p = Planning.objects.filter(nom=nom).first()
            if p:
                return p
            return Planning.objects.create(
                nom=nom, entite_metier=entite, workflow=workflow,
                current_step=step_init, cree_par=cree_par, modifie_par=cree_par,
            )

        planning_dist  = _planning("Planning Distribution Avril 2026 (Démo KPI)", dist, operateur1)
        planning_trans = _planning("Planning Transport Avril 2026 (Démo KPI)", trans, operateur2)
        planning_prod  = _planning("Planning Production Avril 2026 (Démo KPI)", prod, operateur1)

        # ── Ouvrages réels choisis pour la variété du KPI "par ouvrage" ──
        postes_dist = ['BRGM', 'AHALA', 'KOUMASSI', 'BASSA', 'NOMAYOS', 'BEKOKO', 'BERTOUA']
        refs_dist = []
        for poste in postes_dist:
            ref = Reference.objects.filter(
                valeur__startswith='DISTRIBUTION', valeur__icontains=f'_{poste}_'
            ).first()
            if ref:
                refs_dist.append(ref)

        postes_trans = ['LOGBABA', 'MAROUA', 'DEIDO', 'NGAOUNDERE', 'NDJOCK NKONG']
        refs_trans = []
        for poste in postes_trans:
            ref = Reference.objects.filter(
                valeur__startswith='TRANSPORT', valeur__icontains=f'_{poste}_'
            ).first()
            if ref:
                refs_trans.append(ref)

        centrales_ipp = list(Centrale.objects.filter(valeur__in=['KPDC', 'DPDC']))
        centrales_internes = list(Centrale.objects.exclude(valeur__in=['KPDC', 'DPDC']))[:4]

        if not refs_dist or not refs_trans or not centrales_ipp or not centrales_internes:
            self.stdout.write(self.style.ERROR(
                "Référentiel insuffisant (references/centrales). "
                "Lancez d'abord le seed principal (seed_all / seed_referentiel_excel)."
            ))
            return

        avril = lambda jour, heure=8: timezone.make_aware(timezone.datetime(2026, 4, jour, heure, 0))

        # ── Plan de répartition des statuts (aligné avec les KPI du dashboard) ──
        # DISTRIBUTION : 10 VALIDE, 14 TERMINE, 3 REPORTE = 27
        # TRANSPORT    : 5 VALIDE, 6 TERMINE, 2 REPORTE   = 13
        # PRODUCTION   : 5 VALIDE, 6 TERMINE, 2 REPORTE   = 13
        # Total = 53 → programmés 20 / exécutés 26 / non exécutés 7
        def _repartition(n_valide, n_termine, n_reporte):
            return (
                ['VALIDE'] * n_valide +
                ['TERMINE'] * n_termine +
                ['REPORTE'] * n_reporte
            )

        statuts_dist  = _repartition(10, 14, 3)
        statuts_trans = _repartition(5, 6, 2)
        statuts_prod  = _repartition(5, 6, 2)

        created_travaux = {"DISTRIBUTION": [], "TRANSPORT": [], "PRODUCTION": []}

        # ── DISTRIBUTION ──
        for i, statut in enumerate(statuts_dist):
            ref = refs_dist[i % len(refs_dist)]
            jour = 1 + (i % 28)
            heure_debut = avril(jour, 7 + (i % 6))
            travail, _ = Travail.objects.get_or_create(
                planning=planning_dist, reference=ref, heure_debut_planifie=heure_debut,
                defaults={
                    "segment": "DISTRIBUTION",
                    "priorite": ["P1", "P2", "P3"][i % 3],
                    "type_travaux": type_maintenance if i % 2 == 0 else type_reparation,
                    "unite_demanderesse": unite_dist,
                    "consistance_travaux": f"Maintenance réseau {ref.valeur.split('_')[1] if '_' in ref.valeur else ''}",
                    "duree": 4, "unite_duree": "HEURES",
                    "date_programmee": avril(jour).date(),
                    "charge_consignation": charge1,
                    "type_reseau": "HTA",
                    "niveau_coupure": "DEPARTS",
                    "entite_metier": dist,
                    "statut_travaux": statut,
                    "cree_par": operateur1,
                    "modifie_par": operateur1,
                }
            )
            created_travaux["DISTRIBUTION"].append(travail)

        # ── TRANSPORT ──
        for i, statut in enumerate(statuts_trans):
            ref = refs_trans[i % len(refs_trans)]
            jour = 1 + (i % 28)
            heure_debut = avril(jour, 8 + (i % 5))
            travail, _ = Travail.objects.get_or_create(
                planning=planning_trans, reference=ref, heure_debut_planifie=heure_debut,
                defaults={
                    "segment": "TRANSPORT",
                    "priorite": ["P1", "P2", "P3"][i % 3],
                    "type_travaux": type_entretien_trans,
                    "unite_demanderesse": unite_trans,
                    "consistance_travaux": f"Entretien ouvrage {ref.valeur.split('_')[1] if '_' in ref.valeur else ''}",
                    "duree": 6, "unite_duree": "HEURES",
                    "date_programmee": avril(jour).date(),
                    "charge_consignation": charge2,
                    "type_reseau": "HTB",
                    "niveau_coupure": "POSTES",
                    "entite_metier": trans,
                    "statut_travaux": statut,
                    "cree_par": operateur2,
                    "modifie_par": operateur2,
                }
            )
            created_travaux["TRANSPORT"].append(travail)

        # ── PRODUCTION (alterne IPP / interne pour le KPI 6) ──
        for i, statut in enumerate(statuts_prod):
            est_ipp = i % 2 == 0
            unite = unites_ipp[i % len(unites_ipp)] if est_ipp else unites_interne[i % len(unites_interne)]
            centrale = centrales_ipp[i % len(centrales_ipp)] if est_ipp else centrales_internes[i % len(centrales_internes)]
            jour = 1 + (i % 28)
            heure_debut = avril(jour, 6 + (i % 4))
            travail, _ = Travail.objects.get_or_create(
                planning=planning_prod, unite_demanderesse=unite, heure_debut_planifie=heure_debut,
                defaults={
                    "segment": "PRODUCTION",
                    "priorite": ["P1", "P2", "P3"][i % 3],
                    "type_travaux": type_entretien_prod,
                    "consistance_travaux": f"Révision/entretien {centrale.valeur}",
                    "duree": 8, "unite_duree": "HEURES",
                    "date_programmee": avril(jour).date(),
                    "disponibilite_mecanique_mw": 100.0 + i,
                    "prevision_puissance_sollicitee": 80.0 + i,
                    "prevision_puissance_interrompue": 15.0,
                    "centrale_thermique_sollicitee": centrale,
                    "entite_metier": prod,
                    "statut_travaux": statut,
                    "cree_par": operateur1,
                    "modifie_par": operateur1,
                }
            )
            created_travaux["PRODUCTION"].append(travail)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Travaux Avril 2026 : "
            f"{len(created_travaux['DISTRIBUTION'])} Distribution, "
            f"{len(created_travaux['TRANSPORT'])} Transport, "
            f"{len(created_travaux['PRODUCTION'])} Production"
        ))

        # ── Propositions d'alignement ACCEPTEE pour peupler "travaux harmonisés" ──
        tous_travaux = (
            created_travaux["DISTRIBUTION"][:4] +
            created_travaux["TRANSPORT"][:2] +
            created_travaux["PRODUCTION"][:2]
        )
        nb_harmonises = 0
        for i, travail in enumerate(tous_travaux):
            if PropositionAlignement.objects.filter(
                travail_a_modifier=travail, statut=PropositionAlignement.Statut.ACCEPTEE
            ).exists():
                continue
            reference_travail = tous_travaux[(i + 1) % len(tous_travaux)]
            PropositionAlignement.objects.create(
                planning=travail.planning,
                travail_a_modifier=travail,
                travail_reference=reference_travail,
                type_proposition=PropositionAlignement.TypeProposition.ALIGNEMENT_TRAVAUX,
                type_travaux_reference=str(reference_travail.type_travaux) if reference_travail.type_travaux else "",
                type_travaux_a_modifier=str(travail.type_travaux) if travail.type_travaux else "",
                priorite_travail=travail.priorite or "",
                ancien_debut=travail.heure_debut_planifie,
                ancienne_fin=travail.heure_fin_planifie,
                nouveau_debut=travail.heure_debut_planifie,
                nouvelle_fin=travail.heure_fin_planifie,
                raison="Alignement démo KPI — travaux regroupés sur le même créneau.",
                statut=PropositionAlignement.Statut.ACCEPTEE,
                cree_par=operateur1,
            )
            nb_harmonises += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {nb_harmonises} propositions d'alignement ACCEPTEE créées (travaux harmonisés)"))

        total = sum(len(v) for v in created_travaux.values())
        n_valide  = sum(1 for v in created_travaux.values() for t in v if t.statut_travaux == 'VALIDE')
        n_termine = sum(1 for v in created_travaux.values() for t in v if t.statut_travaux == 'TERMINE')
        n_reporte = sum(1 for v in created_travaux.values() for t in v if t.statut_travaux == 'REPORTE')

        self.stdout.write(self.style.SUCCESS(
            f"\n📊 Récapitulatif Avril 2026 : {total} travaux "
            f"({n_valide} programmés / {n_termine} exécutés / {n_reporte} non exécutés)\n"
        ))
