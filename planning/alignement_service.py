from datetime import timedelta, datetime
from .models import Travail, Planning, PropositionAlignement


# HELPERS DE BASE

def _periodes_se_chevauchent(debut_a, fin_a, debut_b, fin_b) -> bool:
    """
    Deux périodes se chevauchent si :
        debut_a < fin_b  ET  fin_a > debut_b
    """
    if not all([debut_a, fin_a, debut_b, fin_b]):
        return False
    return debut_a < fin_b and fin_a > debut_b


def _partage_ressource(travail_a: Travail, travail_b: Travail) -> bool:
    """
    Deux travaux partagent une ressource si :
    1. Même Reference exacte (le cas le plus simple)
    2. OU ils partagent un ReferentielItem commun de type
       POSTE, TRONCON ou OUVRAGE
    """
    
    if not travail_a.reference or not travail_b.reference:
        return False
    
    # cas 1: meme référence
    if travail_a.reference == travail_b.reference:
        return True
    
    #cas 2: items communs(poste, ouvrage, tronçon)
    TYPES_PARTAGES = [ 'POSTE', 'OUVRAGE', 'TRONCON', 'SEGMENT']
    
    items_a = set(
        travail_a.reference.items.filter( # type: ignore[attr-defined]
            type__nom__in=TYPES_PARTAGES
        ).values_lsit('valeur', 'type__nom')
    ) 
    
    items_b = set(
        travail_a.reference.items.filter( # type: ignore[attr-defined]
            type__nom__in=TYPES_PARTAGES
        ).values_lsit('valeur', 'type__nom')
    ) 
    
    # si il y a au moins un item en commun
    
    return bool(items_a & items_b)

def _ressources_communes(travail_a: Travail, travail_b: Travail) -> list:
    """
    Retourne la liste des ressources communes entre deux travaux.
    Utile pour afficher dans la proposition pourquoi ils sont en conflit.
    """
    if not travail_a.reference or not travail_b.reference:
        return []

    TYPES_PARTAGES = ['POSTE', 'TRONCON', 'OUVRAGE', 'SEGMENT']

    items_a = set(
        travail_a.reference.items.filter( # type: ignore[attr-defined]
            type__nom__in=TYPES_PARTAGES
        ).values_list('valeur', 'type__nom')
    )
    items_b = set(
        travail_b.reference.items.filter( # type: ignore[attr-defined]
            type__nom__in=TYPES_PARTAGES
        ).values_list('valeur', 'type__nom')
    )

    communs = items_a & items_b
    return [f"{type_nom} : {valeur}" for valeur, type_nom in communs]

   

def _nom_ressource(travail: Travail) -> str:
    """Retourne le nom lisible de la ressource."""
    if travail.reference:
        return travail.reference.valeur  # ou le champ qui contient le nom
    return "Référence inconnue"


# PRIORITÉ

PRIORITE_ORDRE = {
    'TRANSPORT': 0,
    'P1': 1,
    'P2': 2,
    'P3': 3,
    None: 4,
}


def _peut_bouger(travail: Travail) -> bool:
    """
    Règle métier :
    - TRANSPORT → ne bouge JAMAIS
    - P1 → ne bouge pas (urgent)
    - P2, P3 → peut bouger
    """
    if travail.segment == 'TRANSPORT':
        return False
    if hasattr(travail, 'priorite') and travail.priorite == 'P1':
        return False
    return True


def _score_priorite(travail: Travail) -> int:
    """Score pour trier : plus bas = plus prioritaire = référence."""
    if travail.segment == 'TRANSPORT':
        return PRIORITE_ORDRE['TRANSPORT']
    priorite = getattr(travail, 'priorite', None)
    return PRIORITE_ORDRE.get(priorite, 4)


# COMPATIBILITÉ DES TYPES

TYPES_LOURDS = {
    'REMPLACEMENT', 'CONSTRUCTION', 'REHABILITATION',
    'RENFORCEMENT', 'MONTAGE', 'DEPLACEMENT'
}
TYPES_LEGERS = {
    'INSPECTION', 'CONTROLES GENERAUX', 'NORMALISATION',
    'Normalisations BT', 'Normalisations MT'
}


def _analyser_compatibilite(type_a: str, type_b: str) -> dict:
    """
    Analyse la compatibilité entre deux types de travaux.
    Retourne un niveau et une note explicative.
    """
    if not type_a or not type_b:
        return {"niveau": "INCONNU", "note": "Type non défini, vérification manuelle."}

    if type_a == type_b:
        if type_a in TYPES_LOURDS:
            return {"niveau": "ATTENTION",
                    "note": f"Deux travaux '{type_a}' lourds sur la même ressource. Risque d'interférence."}
        return {"niveau": "OK",
                "note": f"Deux travaux de même type '{type_a}'. Coordonner les équipes."}

    if (type_a in TYPES_LOURDS and type_b in TYPES_LEGERS) or \
       (type_b in TYPES_LOURDS and type_a in TYPES_LEGERS):
        return {"niveau": "OPTIMAL",
                "note": f"'{type_a}' + '{type_b}' : excellente opportunité d'alignement."}

    if type_a in TYPES_LOURDS and type_b in TYPES_LOURDS:
        return {"niveau": "ATTENTION",
                "note": f"Deux travaux lourds. Coordination précise requise."}

    return {"niveau": "OK", "note": f"'{type_a}' + '{type_b}' : alignement possible."}


# CHARGE DE CONSIGNATION

def _charge_disponible(charge, nouveau_debut, nouvelle_fin, exclure_id=None) -> tuple:
    """
    Vérifie si le charge de consignation est libre sur la nouvelle période.

    Logique :
    - On cherche tous ses autres travaux
    - Si l'un d'eux chevauche la nouvelle période → BLOQUÉ
    """
    if not charge:
        return True, ""

    autres_travaux = Travail.objects.filter(
        charge_consignation=charge,
        heure_debut_planifie__isnull=False,
        heure_fin_planifie__isnull=False,
    ).exclude(id=exclure_id)

    for t in autres_travaux:
        if _periodes_se_chevauchent(nouveau_debut, nouvelle_fin,
                                    t.heure_debut_planifie, t.heure_fin_planifie):
            return False, (
                f"{charge.get_full_name()} est déjà affecté au travail "
                f"'{_nom_ressource(t)}' de "
                f"{t.heure_debut_planifie.strftime('%d/%m %H:%M')if t.heure_debut_planifie else None,} "
                f"à {t.heure_fin_planifie.strftime('%d/%m %H:%M')if t.heure_fin_planifie else None,}."
            )
    return True, ""


# DÉTECTION DES GROUPES

def _detecter_groupes(travaux: list) -> list:
    """
    Regroupe les travaux qui :
    1. Partagent la même référence réseau
    2. Ont des périodes qui se chevauchent

    Raisonnement :
    On parcourt tous les travaux. Pour chaque travail non encore visité,
    on cherche tous les autres qui chevauchent avec lui.
    Le résultat est une liste de groupes.
    """
    visites = set()
    groupes = []

    for i, t_a in enumerate(travaux):
        if t_a.id in visites:
            continue
        if not t_a.heure_debut_planifie or not t_a.heure_fin_planifie:
            continue

        groupe = [t_a]
        visites.add(t_a.id)

        for j, t_b in enumerate(travaux):
            if i == j or t_b.id in visites:
                continue
            if not t_b.heure_debut_planifie or not t_b.heure_fin_planifie:
                continue

            if (_partage_ressource(t_a, t_b) and
                _periodes_se_chevauchent(
                    t_a.heure_debut_planifie, t_a.heure_fin_planifie,
                    t_b.heure_debut_planifie, t_b.heure_fin_planifie
                )):
                groupe.append(t_b)
                visites.add(t_b.id)

        if len(groupe) > 1:
            groupes.append(groupe)

    return groupes


def _trouver_reference(groupe: list) -> Travail:
    """
    Trouve le travail de référence dans un groupe.
    Ordre : TRANSPORT > P1 > le plus tôt > le plus long
    """
    return min(groupe, key=lambda t: (
        _score_priorite(t),
        t.heure_debut_planifie,
        -(t.heure_fin_planifie - t.heure_debut_planifie).total_seconds()
    ))


def _calculer_nouvel_horaire(travail: Travail, reference: Travail) -> tuple:
    """
    Calcule le nouvel horaire pour aligner le travail sur la référence.

    Raisonnement :
    - On conserve la durée du travail
    - On essaie de le caler au début de la fenêtre de la référence
    - Si ça dépasse la fin de la référence, on recule pour tenir dans la fenêtre
    """
    
    if (
        travail.heure_fin_planifie is None or
        travail.heure_debut_planifie is None or
        reference.heure_debut_planifie is None or
        reference.heure_fin_planifie is None
    ):
        raise ValueError("les horaires doivent etres definis.")
    
    duree: timedelta = travail.heure_fin_planifie - travail.heure_debut_planifie
    nouveau_debut: datetime = reference.heure_debut_planifie
    nouvelle_fin: datetime = nouveau_debut + duree

    # Si ça dépasse la fenêtre de la référence
    if nouvelle_fin > reference.heure_fin_planifie:
        nouvelle_fin = reference.heure_fin_planifie
        nouveau_debut = nouvelle_fin - duree
        # Si le recul fait sortir du début de fenêtre
        if nouveau_debut < reference.heure_debut_planifie:
            nouveau_debut = reference.heure_debut_planifie
            nouvelle_fin = nouveau_debut + duree

    return nouveau_debut, nouvelle_fin


# FONCTION PRINCIPALE

def analyser_et_proposer(planning: Planning, user) -> dict:
    """
    Analyse les chevauchements d'un planning et génère des propositions.

    Étapes :
    1. Récupérer tous les travaux du planning avec horaires
    2. Détecter les groupes de chevauchement
    3. Pour chaque groupe, trouver la référence ensuite proposer des alignements
    4. Vérifier les contraintes (priorité, charge de consignation)
    5. Sauvegarder et retourner les propositions
    """

    # Supprimer les anciennes propositions EN_ATTENTE
    PropositionAlignement.objects.filter(
        planning=planning,
        statut=PropositionAlignement.Statut.EN_ATTENTE
    ).delete()

    # Récupérer les travaux avec horaires
    travaux = list(
        Travail.objects.filter(planning=planning).select_related(
            'reference', 'charge_consignation', 'type_travaux'
        ).filter(
            heure_debut_planifie__isnull=False,
            heure_fin_planifie__isnull=False
        )
    )

    if len(travaux) < 2:
        return {
            "message": "Pas assez de travaux avec des horaires pour analyser.",
            "chevauchements": [], "propositions": [],
            "resume": {"total_chevauchements": 0, "total_propositions": 0,
                       "propositions_bloquees": 0, "propositions_libres": 0}
        }

    groupes = _detecter_groupes(travaux)

    if not groupes:
        return {
            "message": "Aucun chevauchement détecté.",
            "chevauchements": [], "propositions": [],
            "resume": {"total_chevauchements": 0, "total_propositions": 0,
                       "propositions_bloquees": 0, "propositions_libres": 0}
        }

    propositions_creees = []
    chevauchements_detectes = []
    nb_bloquees = 0

    for groupe in groupes:
        reference = _trouver_reference(groupe)
        autres = [t for t in groupe if t.id != reference.id]
        type_ref = reference.type_travaux.libelle if reference.type_travaux else "Non défini"

        chevauchements_detectes.append({
            "reference": {
                "id": str(reference.id),
                "ressource": _nom_ressource(reference),
                "segment": reference.segment,
                "priorite": getattr(reference, 'priorite', None),
                "type_travaux": type_ref,
                "debut": reference.heure_debut_planifie.strftime('%d/%m/%Y %H:%M') if reference.heure_debut_planifie else None,
                "fin": reference.heure_fin_planifie.strftime('%d/%m/%Y %H:%M') if reference.heure_fin_planifie else None,
                "peut_bouger": _peut_bouger(reference),
                #detail des composants de la reference
                "composants": list(
                    reference.reference.items.values('type__nom', 'valeur') # type: ignore
                ) if reference.reference else []
            },
            "travaux_en_conflit": [{
                "id": str(t.id),
                "ressource": _nom_ressource(t),
                "segment": t.segment,
                "priorite": getattr(t, 'priorite', None),
                "type_travaux": t.type_travaux.libelle if t.type_travaux else "Non défini",
                "debut": t.heure_debut_planifie.strftime('%d/%m/%Y %H:%M'),
                "fin": t.heure_fin_planifie.strftime('%d/%m/%Y %H:%M'),
                "peut_bouger": _peut_bouger(t),
                #Ressources spécifiquement partagées avec la référence
                "ressources_communes": _ressources_communes(reference, t),
            } for t in autres]
        })

        for travail in autres:
            type_travail = travail.type_travaux.libelle if travail.type_travaux else ""

            # Travail ne peut pas bouger → signaler sans proposer de déplacement
            if not _peut_bouger(travail):
                proposition = PropositionAlignement.objects.create(
                    planning=planning,
                    travail_a_modifier=travail,
                    travail_reference=reference,
                    type_proposition=PropositionAlignement.TypeProposition.ALIGNEMENT_TRANSPORT
                        if reference.segment == 'TRANSPORT'
                        else PropositionAlignement.TypeProposition.ALIGNEMENT_TRAVAUX,
                    type_travaux_reference=type_ref,
                    type_travaux_a_modifier=type_travail,
                    priorite_travail=getattr(travail, 'priorite', '') or '',
                    ancien_debut=travail.heure_debut_planifie,
                    ancienne_fin=travail.heure_fin_planifie,
                    nouveau_debut=travail.heure_debut_planifie,
                    nouvelle_fin=travail.heure_fin_planifie,
                    raison=(
                        f"Travail '{_nom_ressource(travail)}' ({travail.segment} - "
                        f"{getattr(travail, 'priorite', 'N/A')}) ne peut pas être déplacé. "
                        f"Chevauchement avec '{_nom_ressource(reference)}'. "
                        f"Résolution manuelle requise."
                    ),
                    statut=PropositionAlignement.Statut.BLOQUEE,
                    cree_par=user
                )
                propositions_creees.append(proposition)
                nb_bloquees += 1
                continue

            # Calculer le nouvel horaire
            nouveau_debut, nouvelle_fin = _calculer_nouvel_horaire(travail, reference)

            # Analyser la compatibilité des types
            compatibilite = _analyser_compatibilite(type_ref, type_travail)

            # Vérifier la disponibilité du charge de consignation
            disponible, detail_conflit = _charge_disponible(
                travail.charge_consignation,
                nouveau_debut, nouvelle_fin,
                exclure_id=travail.id
            )
            ressources = _ressources_communes(reference, travail)
            ressources_str = ", ".join(ressources) if ressources else _nom_ressource(reference)
            raison = (
                f"Chevauchement détecté sur {ressources_str}. "
                f"Référence : '{_nom_ressource(reference)}' ({reference.segment}) "
                f"de {reference.heure_debut_planifie.strftime('%d/%m/%Y %H:%M')if reference.heure_debut_planifie else None,} "
                f"à {reference.heure_fin_planifie.strftime('%d/%m/%Y %H:%M')if reference.heure_fin_planifie else None,}. "
                f"Proposition : déplacer de "
                f"{travail.heure_debut_planifie.strftime('%d/%m/%Y %H:%M')} "
                f"-> {nouveau_debut.strftime('%d/%m/%Y %H:%M')}."
            )
            if not disponible:
                raison += f" CONFLIT CHARGE : {detail_conflit}"

            statut_final = (
                PropositionAlignement.Statut.BLOQUEE
                if not disponible
                else PropositionAlignement.Statut.EN_ATTENTE
            )
            if not disponible:
                nb_bloquees += 1

            proposition = PropositionAlignement.objects.create(
                planning=planning,
                travail_a_modifier=travail,
                travail_reference=reference,
                type_proposition=(
                    PropositionAlignement.TypeProposition.ALIGNEMENT_TRANSPORT
                    if reference.segment == 'TRANSPORT'
                    else PropositionAlignement.TypeProposition.ALIGNEMENT_TRAVAUX
                ),
                type_travaux_reference=type_ref,
                type_travaux_a_modifier=type_travail,
                priorite_travail=getattr(travail, 'priorite', '') or '',
                ancien_debut=travail.heure_debut_planifie,
                ancienne_fin=travail.heure_fin_planifie,
                nouveau_debut=nouveau_debut,
                nouvelle_fin=nouvelle_fin,
                raison=raison,
                note_compatibilite_types=f"[{compatibilite['niveau']}] {compatibilite['note']}",
                conflit_charge_consignation=not disponible,
                detail_conflit=detail_conflit,
                statut=statut_final,
                cree_par=user
            )
            propositions_creees.append(proposition)

    nb_libres = len(propositions_creees) - nb_bloquees

    return {
        "message": (
            f"{len(groupes)} chevauchement(s) détecté(s). "
            f"{len(propositions_creees)} proposition(s) : "
            f"{nb_libres} libre(s), {nb_bloquees} bloquée(s)."
        ),
        "chevauchements": chevauchements_detectes,
        "propositions": propositions_creees,
        "resume": {
            "total_chevauchements": len(groupes),
            "total_propositions": len(propositions_creees),
            "propositions_bloquees": nb_bloquees,
            "propositions_libres": nb_libres,
        }
    }