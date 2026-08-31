"""
Service de calcul du rapport "Suivi des travaux prévisionnels" (KPI direction).

Reproduit les sections du tableau de bord de référence (tuiles de synthèse +
5 tableaux : par région/mois, évolution mois M vs M-1, nombre par
segment/mois, durée des interruptions par segment, travaux exécutés en
alignement).

Conventions retenues (le tableau de bord source ne les documente pas) :
- `annee`/`mois` désignent le "Mois M" de référence pour les comparaisons
  M vs M-1. Les tableaux couvrent la période cumulée du 1er janvier de
  `annee` jusqu'à la fin de `mois` (year-to-date), les tuiles "Mois M"
  couvrent uniquement `mois`.
- "Gain / Réalisation END alignée" = somme de `end_realise_mwh` (à défaut
  `prevision_enf_mwh`) des travaux TERMINE avec `travail_en_alignement=True` :
  l'énergie non distribuée valorisée sur les travaux effectivement regroupés.
- "Taux de conformité planning référence" = part des travaux planifiés sur la
  période qui ont été exécutés sans jamais avoir été reportés
  (`date_report_travaux` vide).
- La région d'un travail est celle de sa Reference (Distribution/Transport)
  ou de sa Centrale sollicitée (Production) — cf. `_get_poste_from_travail`
  dans referentiel/kpi_service.py qui applique la même distinction par segment.
"""
from calendar import monthrange
from collections import OrderedDict, defaultdict
from datetime import date

from django.db.models import Case, DecimalField, F, Sum, When

from .models import Travail

SEGMENTS_PRINCIPAUX = ['TRANSPORT', 'DISTRIBUTION', 'PRODUCTION']
SEGMENTS_AVEC_DACOR = ['DACOR', 'TRANSPORT', 'DISTRIBUTION', 'PRODUCTION']

MOIS_LIBELLES = [
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
]


def _mois_precedent(annee, mois):
    if mois == 1:
        return annee - 1, 12
    return annee, mois - 1


def _bornes_mois(annee, mois):
    debut = date(annee, mois, 1)
    fin = date(annee, mois, monthrange(annee, mois)[1])
    return debut, fin


def _duree_planifiee_expr():
    """Expression ORM convertissant `duree` en heures selon `unite_duree`."""
    return Case(
        When(unite_duree='JOURS', then=F('duree') * 24),
        When(unite_duree='SEMAINES', then=F('duree') * 168),
        default=F('duree'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _gain_end_alignee_expr():
    """END réalisée si saisie, sinon END prévisionnelle, sur travaux alignés."""
    return Case(
        When(end_realise_mwh__isnull=False, then=F('end_realise_mwh')),
        default=F('prevision_enf_mwh'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _somme(qs, expr):
    total = qs.aggregate(total=Sum(expr))['total']
    return float(total) if total is not None else 0.0


def _round2(valeur):
    return round(valeur, 2) if valeur is not None else 0.0


def _format_hhmm(heures_decimal):
    """Convertit une durée décimale en heures (ex: 10.65) en 'H:MM' (10:39)."""
    if not heures_decimal:
        return "0:00"
    total_minutes = round(float(heures_decimal) * 60)
    h, m = divmod(total_minutes, 60)
    return f"{h}:{m:02d}"


def _gain_end_alignee(qs):
    qs_alignes = qs.filter(travail_en_alignement=True, statut_travaux='TERMINE')
    return _round2(_somme(qs_alignes, _gain_end_alignee_expr()))


def _evolution_par_segment(qs_ytd_m, qs_m, qs_ytd_m1):
    """Table B : Evolution des TP mois en cours Vs M-1, par segment + Total."""
    lignes = []
    totaux = defaultdict(float)
    totaux['travaux_planifies'] = 0
    totaux['tp_m1_ytd_m1'] = 0
    totaux['tp_execution'] = 0
    totaux['tp_conformes'] = 0
    totaux['gain_end_mwh'] = 0.0

    for segment in SEGMENTS_PRINCIPAUX:
        qs_seg_m = qs_m.filter(segment=segment)
        qs_seg_m1 = qs_ytd_m1.filter(segment=segment)

        planifies = qs_seg_m.count()
        m1 = qs_seg_m1.count()
        executes = qs_seg_m.filter(statut_travaux='TERMINE').count()
        conformes = qs_seg_m.filter(statut_travaux='TERMINE', date_report_travaux__isnull=True).count()
        gain_end = _gain_end_alignee(qs_seg_m)

        taux_execution = _round2(executes / planifies * 100) if planifies else 0.0
        taux_conformite = _round2(conformes / planifies * 100) if planifies else 0.0

        lignes.append({
            "segment": segment,
            "travaux_planifies": planifies,
            "tp_m1_ytd_m1": m1,
            "taux_execution_travaux_pct": taux_execution,
            "taux_conformite_planning_reference_pct": taux_conformite,
            "gain_end_alignes_tpd_mwh": gain_end,
        })

        totaux['travaux_planifies'] += planifies
        totaux['tp_m1_ytd_m1'] += m1
        totaux['tp_execution'] += executes
        totaux['tp_conformes'] += conformes
        totaux['gain_end_mwh'] += gain_end

    total_planifies = totaux['travaux_planifies']
    total = {
        "segment": "Total",
        "travaux_planifies": total_planifies,
        "tp_m1_ytd_m1": totaux['tp_m1_ytd_m1'],
        "taux_execution_travaux_pct": _round2(totaux['tp_execution'] / total_planifies * 100) if total_planifies else 0.0,
        "taux_conformite_planning_reference_pct": _round2(totaux['tp_conformes'] / total_planifies * 100) if total_planifies else 0.0,
        "gain_end_alignes_tpd_mwh": _round2(totaux['gain_end_mwh']),
    }

    return lignes, total


def _nombre_par_segment_et_mois(qs_ytd, annee, mois):
    """Table C : Nombre TP/segment et mois, par segment + Total, colonnes 1..mois."""
    compteur = defaultdict(int)
    for row in qs_ytd.values('segment', 'date_programmee'):
        date_programmee = row['date_programmee']
        if not date_programmee:
            continue
        compteur[(row['segment'], date_programmee.month)] += 1

    lignes = []
    totaux_mois = defaultdict(int)
    for segment in SEGMENTS_AVEC_DACOR:
        par_mois = OrderedDict()
        total_segment = 0
        for m in range(1, mois + 1):
            val = compteur.get((segment, m), 0)
            par_mois[MOIS_LIBELLES[m - 1]] = val
            total_segment += val
            totaux_mois[MOIS_LIBELLES[m - 1]] += val
        lignes.append({"segment": segment, "par_mois": par_mois, "total": total_segment})

    total_general = sum(totaux_mois.values())
    ligne_total = {"segment": "Total", "par_mois": dict(totaux_mois), "total": total_general}

    return lignes, ligne_total


def _total_tp_par_region_et_mois(qs_ytd, annee, mois):
    """Table A : Total TP par région et Mois."""
    compteur = defaultdict(int)
    rows = qs_ytd.values(
        'segment', 'date_programmee',
        'reference__region__code',
        'centrale_thermique_sollicitee__region__code',
    )
    for row in rows:
        date_programmee = row['date_programmee']
        if not date_programmee:
            continue
        if row['segment'] == 'PRODUCTION':
            region = row['centrale_thermique_sollicitee__region__code'] or "Sans région"
        else:
            region = row['reference__region__code'] or "Sans région"
        compteur[(region, date_programmee.month)] += 1

    regions = sorted({region for region, _mois in compteur.keys()})

    lignes = []
    totaux_mois = defaultdict(int)
    for region in regions:
        par_mois = OrderedDict()
        total_region = 0
        for m in range(1, mois + 1):
            val = compteur.get((region, m), 0)
            par_mois[MOIS_LIBELLES[m - 1]] = val
            total_region += val
            totaux_mois[MOIS_LIBELLES[m - 1]] += val
        lignes.append({"region": region, "par_mois": par_mois, "total": total_region})

    total_general = sum(totaux_mois.values())
    ligne_total = {"region": "Total", "par_mois": dict(totaux_mois), "total": total_general}

    return lignes, ligne_total


def _duree_interruptions_par_segment(qs_ytd):
    """Table D : Durée des interruptions TP par segment."""
    lignes = []
    totaux = defaultdict(float)
    totaux['n_prevue'] = 0
    totaux['n_realisee'] = 0

    for segment in SEGMENTS_AVEC_DACOR:
        qs_seg = qs_ytd.filter(segment=segment)

        indispo_prevue = _somme(qs_seg.filter(duree__isnull=False), _duree_planifiee_expr())
        indispo_realisee = _somme(qs_seg, F('duree_reelle_heures'))

        n_prevue = qs_seg.filter(duree__isnull=False).count()
        n_realisee = qs_seg.filter(duree_reelle_heures__isnull=False).count()

        duree_moy_prevue = indispo_prevue / n_prevue if n_prevue else 0.0
        duree_moy_realisee = indispo_realisee / n_realisee if n_realisee else 0.0

        lignes.append({
            "segment": segment,
            "indisponibilite_prevue_h": _round2(indispo_prevue),
            "indisponibilite_realisee_h": _round2(indispo_realisee),
            "duree_moyenne_prevue_h": _round2(duree_moy_prevue),
            "duree_moyenne_prevue_hhmm": _format_hhmm(duree_moy_prevue),
            "duree_moyenne_realisee_h": _round2(duree_moy_realisee),
            "duree_moyenne_realisee_hhmm": _format_hhmm(duree_moy_realisee),
        })

        totaux['indispo_prevue'] = totaux.get('indispo_prevue', 0.0) + indispo_prevue
        totaux['indispo_realisee'] = totaux.get('indispo_realisee', 0.0) + indispo_realisee
        totaux['n_prevue'] += n_prevue
        totaux['n_realisee'] += n_realisee

    duree_moy_prevue_totale = totaux.get('indispo_prevue', 0.0) / totaux['n_prevue'] if totaux['n_prevue'] else 0.0
    duree_moy_realisee_totale = totaux.get('indispo_realisee', 0.0) / totaux['n_realisee'] if totaux['n_realisee'] else 0.0

    total = {
        "segment": "Total",
        "indisponibilite_prevue_h": _round2(totaux.get('indispo_prevue', 0.0)),
        "indisponibilite_realisee_h": _round2(totaux.get('indispo_realisee', 0.0)),
        "duree_moyenne_prevue_h": _round2(duree_moy_prevue_totale),
        "duree_moyenne_prevue_hhmm": _format_hhmm(duree_moy_prevue_totale),
        "duree_moyenne_realisee_h": _round2(duree_moy_realisee_totale),
        "duree_moyenne_realisee_hhmm": _format_hhmm(duree_moy_realisee_totale),
    }

    return lignes, total


def _travaux_executes_en_alignement(qs_ytd):
    """Table E : Travaux exécutés en alignement."""
    qs_alignes = qs_ytd.filter(travail_en_alignement=True, statut_travaux='TERMINE')

    lignes = []
    total_travaux = 0
    total_duree = 0.0
    for segment in SEGMENTS_PRINCIPAUX:
        qs_seg = qs_alignes.filter(segment=segment)
        n = qs_seg.count()
        if n == 0:
            continue
        duree = _somme(qs_seg, F('duree_reelle_heures'))
        lignes.append({
            "segment": segment,
            "total_travaux": n,
            "status": "Exécuté en alignement",
            "duree_realisee_h": _round2(duree),
        })
        total_travaux += n
        total_duree += duree

    total = {
        "segment": "Total",
        "total_travaux": total_travaux,
        "status": "",
        "duree_realisee_h": _round2(total_duree),
    }

    return lignes, total


def generer_rapport_suivi(annee, mois, queryset=None):
    """Construit le rapport complet "Suivi des travaux prévisionnels" pour
    le mois M = `mois`/`annee`, avec tableaux cumulés du 1er janvier à la
    fin de ce mois. `queryset` permet de restreindre la base (permissions,
    filtre planning) ; par défaut tous les travaux."""
    qs = Travail.objects.all() if queryset is None else queryset

    annee_m1, mois_m1 = _mois_precedent(annee, mois)

    debut_mois_m, fin_mois_m = _bornes_mois(annee, mois)
    debut_annee = date(annee, 1, 1)
    _debut_m1, fin_mois_m1 = _bornes_mois(annee_m1, mois_m1)

    qs_ytd = qs.filter(date_programmee__gte=debut_annee, date_programmee__lte=fin_mois_m)
    qs_m = qs.filter(date_programmee__gte=debut_mois_m, date_programmee__lte=fin_mois_m)
    qs_ytd_m1 = qs.filter(date_programmee__gte=debut_annee, date_programmee__lte=fin_mois_m1)

    evolution_lignes, evolution_total = _evolution_par_segment(qs_ytd, qs_m, qs_ytd_m1)
    nombre_lignes, nombre_total = _nombre_par_segment_et_mois(qs_ytd, annee, mois)
    region_lignes, region_total = _total_tp_par_region_et_mois(qs_ytd, annee, mois)
    interruptions_lignes, interruptions_total = _duree_interruptions_par_segment(qs_ytd)
    alignement_lignes, alignement_total = _travaux_executes_en_alignement(qs_ytd)

    # ── Tuiles de synthèse (réutilisent les agrégats déjà calculés) ──
    executes_mois_m = qs_m.filter(statut_travaux='TERMINE').count()
    duree_moy_realisee_mois_m = (
        _somme(qs_m.filter(statut_travaux='TERMINE'), F('duree_reelle_heures'))
        / executes_mois_m
    ) if executes_mois_m else 0.0

    tuiles = {
        "travaux_planifies_total_ytd": qs_ytd.count(),
        "tp_m1_ytd_m1": qs_ytd_m1.count(),
        "execute_mois_m": executes_mois_m,
        "taux_execution_tp_pct": evolution_total["taux_execution_travaux_pct"],
        "taux_conformite_mois_m_pct": evolution_total["taux_conformite_planning_reference_pct"],
        "duree_moyenne_prevue_h": interruptions_total["duree_moyenne_prevue_h"],
        "duree_moyenne_prevue_hhmm": interruptions_total["duree_moyenne_prevue_hhmm"],
        "duree_moyenne_realisee_mois_m_h": _round2(duree_moy_realisee_mois_m),
        "duree_moyenne_realisee_mois_m_hhmm": _format_hhmm(duree_moy_realisee_mois_m),
        "tp_execute_alignement_ytd": alignement_total["total_travaux"],
        "tp_non_executes_ytd": qs_ytd.filter(statut_travaux='REPORTE').count(),
        "tp_annules_ytd": qs_ytd.filter(statut_travaux='ANNULE').count(),
        "end_evitee_tpd_alignes_ytd_mwh": evolution_total["gain_end_alignes_tpd_mwh"],
        "realisation_end_alignee_mois_m_mwh": _gain_end_alignee(qs_m),
    }

    return {
        "periode": {
            "annee": annee,
            "mois": mois,
            "mois_libelle": f"{MOIS_LIBELLES[mois - 1].capitalize()} {annee}",
            "annee_m1": annee_m1,
            "mois_m1": mois_m1,
        },
        "tuiles": tuiles,
        "total_tp_par_region_et_mois": {
            "colonnes_mois": MOIS_LIBELLES[:mois],
            "lignes": region_lignes,
            "total": region_total,
        },
        "evolution_tp_par_segment": {
            "lignes": evolution_lignes,
            "total": evolution_total,
        },
        "nombre_tp_par_segment_et_mois": {
            "colonnes_mois": MOIS_LIBELLES[:mois],
            "lignes": nombre_lignes,
            "total": nombre_total,
        },
        "duree_interruptions_par_segment": {
            "lignes": interruptions_lignes,
            "total": interruptions_total,
        },
        "travaux_executes_en_alignement": {
            "lignes": alignement_lignes,
            "total": alignement_total,
        },
    }
