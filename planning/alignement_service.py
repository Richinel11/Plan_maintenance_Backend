from django.utils import timezone
import calendar
from datetime import timedelta, datetime
from .models import Travail, Planning, PropositionAlignement


# HELPERS DE BASE

ALIGNEMENT_COMPATIBLE = {
    'TRANSPORT': ['TRANSPORT', 'DISTRIBUTION_POSTE_SOURCE', 'DISTRIBUTION_LIGNE', 'PRODUCTION'],
    'DISTRIBUTION_POSTE_SOURCE': ['DISTRIBUTION_POSTE_SOURCE', 'DISTRIBUTION_LIGNE'],
    'DISTRIBUTION_LIGNE': ['DISTRIBUTION_LIGNE'],
    'PRODUCTION': ['TRANSPORT', 'PRODUCTION'],
}

def _periodes_se_chevauchent(debut_a, fin_a, debut_b, fin_b) -> bool:
    """
    Deux périodes se chevauchent si :
        debut_a < fin_b  ET  fin_a > debut_b
    """
    if not all([debut_a, fin_a, debut_b, fin_b]):
        return False
    return debut_a < fin_b and fin_a > debut_b

# Trouver la region elecrique d'un travail à partir de sa référence
def _get_region(travail: Travail) -> str| None:
    if not travail.reference or not travail.reference.region:
        return None
    return travail.reference.region.code

# Trouver le poste d'un travail à partir de sa référence
def _get_poste(travail: Travail) -> str| None:
    if not travail.reference:
        return None
    item = travail.reference.items.filter(type__nom='POSTE').first() # type: ignore[attr-defined]
    return item.valeur if item else None

# Trouver la rame d'un travail à partir de sa référence
def _get_rame(travail: Travail) -> str| None:
    if not travail.reference:
        return None
    item = travail.reference.items.filter(type__nom='RAME').first() # type: ignore[attr-defined]
    return item.valeur if item else None

# Trouver la region elecrique d'un travail à partir de sa référence
def _get_depart(travail: Travail) -> str| None:
    if not travail.reference:
        return None 
    item = travail.reference.items.filter(type__nom='DEPART').first() # type: ignore[attr-defined]
    return item.valeur if item else None

def _est_coupure_au_poste(travail: Travail) -> bool:
    """travaux transport coupe toujours au niveau du poste, quel que soit le champ niveau_coupure."""
    if travail.segment == 'TRANSPORT':
        return True
    return travail.niveau_coupure == 'POSTE' # type: ignore[attr-defined]



def _nom_ressource(travail: Travail) -> str:
    """Retourne le nom lisible de la ressource."""
    
    poste = _get_poste(travail)
    rame = _get_rame(travail)
    depart = _get_depart(travail)
    if depart:
         return f"{poste} / {rame or ''} / {depart}".replace(' / / ', ' / ')
    if rame : 
         return f"{poste} / {rame}"  
    return poste or (travail.reference.valeur if travail.reference else str(travail.id))



def _partage_ressource(travail_a: Travail, travail_b: Travail) -> bool:
    """
    Implémente les 3 cas d'alignement :
    1. Coupure poste ↔ n'importe quoi sur ce poste → compatible
    2. Coupure rame ↔ rame identique ou départ de cette rame → compatible
    3. Coupure départ ↔ exactement le même départ → compatible
    Toujours après vérification région + poste identiques.
    La Production est exclue de l'alignement pour le moment.
    """
    # on exclut la production pour le moment
    if travail_a.type_alignement == 'PRODUCTION' or travail_b.type_alignement == 'PRODUCTION':
        return False
    
    # on recupere les regions et postes des deux travaux
    region_a = _get_region(travail_a)
    region_b = _get_region(travail_b)
    # Si l'une des references n'a pas de région connue, pas d'alignement possible.
    if not region_a or not region_b or region_a != region_b:
        return False
    
    poste_a = _get_poste(travail_a)
    poste_b = _get_poste(travail_b)
    if not poste_a or not poste_b or poste_a != poste_b:
        return False
    
    # Cas 1 : l'un des deux coupe tout le poste
    if _est_coupure_au_poste(travail_a) or _est_coupure_au_poste(travail_b):
        return True
    
    rame_a = _get_rame(travail_a)
    rame_b = _get_rame(travail_b)
    depart_a = _get_depart(travail_a)
    depart_b = _get_depart(travail_b)
    
    coupure_a = travail_a.niveau_coupure # type: ignore[attr-defined]
    coupure_b = travail_b.niveau_coupure # type: ignore[attr-defined]
    
     # Cas 2 : coupure rame → compatible si même rame ou même départ de rame
    if coupure_a == 'RAME' and coupure_b == 'RAME':
        return bool(rame_a) and rame_a == rame_b
    if coupure_a == 'RAME' and coupure_b == 'DEPART':
        return bool(rame_a) and rame_a == rame_b
    if coupure_b == 'RAME' and coupure_a == 'DEPART':
        return bool(rame_b) and rame_a == rame_b
    
    # cas 3 : coupure départ → compatible si même départ
    if coupure_a == 'DEPART' and coupure_b == 'DEPART':
        return bool(depart_a) and depart_a == depart_b
    
    return False 

 # PRIORITÉ
PRIORITE_ORDRE = {'TRANSPORT': 0,'P1': 1,'P2': 2,'P3': 3,None: 4,}


def _peut_bouger(travail: Travail) -> bool:
    """
    Règle métier :
    - TRANSPORT → ne bouge JAMAIS
    - P1 → ne bouge pas (urgent)
    - P2, P3 → peut bouger
    """
    if travail.segment == 'TRANSPORT':
        return False
    if travail.priorite == 'P1': # type: ignore[attr-defined]
        return False
    return True

def _score_priorite(travail: Travail) -> int:
    """retourne un score numérique pour la priorité d'un travail, plus bas = plus prioritaire"""
    if travail.segment == 'TRANSPORT':
        return PRIORITE_ORDRE['TRANSPORT']
    return PRIORITE_ORDRE.get(travail.priorite, 4) #type: ignore[attr-defined]

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
                f"'{_nom_ressource(t)}' de {t.heure_debut_planifie.strftime('%d/%m %H:%M') if t.heure_debut_planifie else '?'} "
                f"à {t.heure_fin_planifie.strftime('%d/%m %H:%M') if t.heure_fin_planifie else '?'}."
            )
    return True, ""


def _ressources_communes(travail_a: Travail, travail_b: Travail) -> list:
    """
    Retourne la liste des ressources communes entre deux travaux.
    """
    if not travail_a.reference or not travail_b.reference:
        return []

    TYPES_CONTROLES = ['POSTE', 'TRONCON', 'OUVRAGE', 'SEGMENT']

    items_a = set(
        travail_a.reference.items  # type: ignore[attr-defined]
        .filter(type__nom__in=TYPES_CONTROLES
        ).values_list('valeur', 'type__nom')
    )
    items_b = set(
        travail_b.reference.items # type: ignore[attr-defined]
        .filter(type__nom__in=TYPES_CONTROLES
        ).values_list('valeur', 'type__nom')
    )

    communs = items_a & items_b
    return [f"{type_nom} : {valeur}" for valeur, type_nom in communs]

   

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




# DÉTECTION DES GROUPES
def _detecter_groupes(travaux: list) -> list:
    """
    Détecte les composantes connexes : si A-B sont liés et B-C sont liés,
    les trois forment un seul groupe même si A et C ne sont pas directement
    liés. C'est volontaire : déplacer B pour le caler sur A peut recréer
    un conflit avec C, donc les trois doivent être traités ensemble pour
    qu'une seule proposition cohérente en sorte.
    """
    n = len(travaux)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for i in range(n):
        t_a = travaux[i]
        if not t_a.heure_debut_planifie or not t_a.heure_fin_planifie:
            continue
        for j in range(i + 1, n):
            t_b = travaux[j]
            if not t_b.heure_debut_planifie or not t_b.heure_fin_planifie:
                continue
            if (_partage_ressource(t_a, t_b) and
                _periodes_se_chevauchent(
                    t_a.heure_debut_planifie, t_a.heure_fin_planifie,
                    t_b.heure_debut_planifie, t_b.heure_fin_planifie
                )):
                union(i, j)

    groupes_par_racine = {}
    for i, t in enumerate(travaux):
        if not t.heure_debut_planifie or not t.heure_fin_planifie:
            continue
        racine = find(i)
        groupes_par_racine.setdefault(racine, []).append(t)

    return [g for g in groupes_par_racine.values() if len(g) > 1]

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


def _duree_en_heures(travail: Travail) -> timedelta:
    
    """
    Calcule la durée du travail en timedelta.
    Gère heures, jours et semaines.
    """
    #cas où les heures de début et de fin sont définies
    if travail.heure_debut_planifie and travail.heure_fin_planifie:
        duree = travail.heure_fin_planifie - travail.heure_debut_planifie
        
        # au cas du passage de minuit
        if duree.total_seconds() < 0:
            duree += timedelta(days=1)
        
        return duree
    
    #Fallback sur le champ duree + unite_duree
    if travail.duree is None:
        return timedelta(hours=4) # durée par defaut
    
    if travail.unite_duree == 'HEURES':
        return timedelta(hours=travail.duree)
    elif travail.unite_duree == 'JOURS':
        return timedelta(days=travail.duree)
    elif travail.unite_duree == 'SEMAINES':
        return timedelta(weeks=travail.duree)
    return timedelta(hours=travail.duree)
    

def _calculer_nouvel_horaire(travail: Travail, reference: Travail) -> tuple:
    """
    Aligne un travail sur une fenêtre de référence tout en conservant sa durée.

    """
    if not travail.heure_debut_planifie or not travail.heure_fin_planifie:
        return reference.heure_debut_planifie, reference.heure_fin_planifie
    if not reference.heure_debut_planifie or not reference.heure_fin_planifie:
        return travail.heure_debut_planifie, travail.heure_fin_planifie
    
    duree: timedelta = _duree_en_heures(travail)
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

# ======================================================================
# FONCTION PRINCIPALE
#=======================================================================

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
            'reference', 'reference__region','charge_consignation', 'type_travaux'
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

            # Travail ne peut pas bouger -> signaler sans proposer de déplacement
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
                    priorite_travail=travail.priorite or '',
                    ancien_debut=travail.heure_debut_planifie,
                    ancienne_fin=travail.heure_fin_planifie,
                    nouveau_debut=travail.heure_debut_planifie,
                    nouvelle_fin=travail.heure_fin_planifie,
                    raison=f"'{_nom_ressource(travail)}' ne peut pas être déplacé (priorité {travail.priorite}). Conflit avec '{_nom_ressource(reference)}' Résolution manuelle requise.",
                    statut=PropositionAlignement.Statut.BLOQUEE, 
                    cree_par=user
                )
                propositions_creees.append(proposition)
                nb_bloquees += 1
                continue

            # Calculer le nouvel horaire
            nouveau_debut, nouvelle_fin = _calculer_nouvel_horaire(travail, reference)

            # Analyser la compatibilité des types de travaux 
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
                f"de {reference.heure_debut_planifie.strftime('%d/%m/%Y %H:%M')if reference.heure_debut_planifie else None} "
                f"à {reference.heure_fin_planifie.strftime('%d/%m/%Y %H:%M')if reference.heure_fin_planifie else None}. "
                f"Proposition : déplacer l'heure de début de "
                f"{travail.heure_debut_planifie.strftime('%d/%m/%Y %H:%M')} -> {nouveau_debut.strftime('%d/%m/%Y %H:%M')}."
            )
            if not disponible:
                raison += f" CONFLIT CHARGE : {detail_conflit}"

            statut_final = (PropositionAlignement.Statut.BLOQUEE if not disponible else PropositionAlignement.Statut.EN_ATTENTE)
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
    
 #=======================================   
 # FONCTIONS POUR L'ALIGNEMENT PAR MOIS
 #=======================================   
    
def get_fenetre_mois(annee: int= None, mois: int= None) -> tuple: # type: ignore[attr-defined]
    """
    Retourne le début et la fin du mois demandé.
    Par défaut : mois en cours.
    """
    now = timezone.now()
    annee = annee or now.year
    mois = mois or now.month
    
    debut_mois = timezone.make_aware(datetime(annee, mois, 1,0,0,0))
    dernier_jour = calendar.monthrange(annee, mois)[1]
    fin_mois =  timezone.make_aware(datetime(annee, mois, dernier_jour, 23,59,59))
    
    return debut_mois, fin_mois    
    
def analyser_mois(user, annee: int = None, mois: int = None) -> dict:
    """
    Analyse les chevauchements entre TOUS les travaux qui touchent
    le mois demandé:
    heure_debut_planifie <= fin_du_mois
     heure_fin_planifie  >= debut_du_mois

    Cela capture les travaux qui :
    - commencent et finissent dans le mois
    - commencent avant le mois mais finissent dedans
    - commencent dans le mois mais finissent après
    - commencent avant et finissent après (chevauchent tout le mois)
    """

    debut_mois, fin_mois = get_fenetre_mois(annee, mois)  # type: ignore[attr-defined]

    # tout travail qui touche le mois courant
    travaux = list(
        Travail.objects.filter(
            heure_debut_planifie__isnull=False,
            heure_fin_planifie__isnull=False,
            heure_debut_planifie__lte=fin_mois,    # commence avant la fin du mois
            heure_fin_planifie__gte=debut_mois,    # finit après le début du mois
        ).select_related(
            'reference', 'reference__region',
            'charge_consignation', 'type_travaux', 'planning'
        )
    )
    
    nb_travaux = len(travaux)
    periode = f"{debut_mois.strftime('%d/%m/%Y')} jusqu'au -> {fin_mois.strftime('%d/%m/%Y')}"

    if nb_travaux < 2:
        return {
            "message": f"Pas assez de travaux sur la période {periode}.",
            "periode": periode,
            "chevauchements": [], "propositions": [],
            "resume": {
                "periode": periode,
                "total_travaux_analyses": nb_travaux,
                "total_chevauchements": 0,
                "total_propositions": 0,
                "propositions_bloquees": 0,
                "propositions_libres": 0,
            }
        }

    groupes = _detecter_groupes(travaux)

    if not groupes:
        return {
            "message": f"Aucun chevauchement détecté sur la période {periode}.",
            "periode": periode,
            "chevauchements": [], "propositions": [],
            "resume": {
                "periode": periode,
                "total_travaux_analyses": nb_travaux,
                "total_chevauchements": 0,
                "total_propositions": 0,
                "propositions_bloquees": 0,
                "propositions_libres": 0,
            }
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
                "planning_nom": reference.planning.nom,
                "ressource": _nom_ressource(reference),
                "segment": reference.segment,
                "priorite": reference.priorite,
                "type_travaux": type_ref,
                "debut": reference.heure_debut_planifie.strftime('%d/%m/%Y %H:%M') if reference.heure_debut_planifie else None,
                "fin": reference.heure_fin_planifie.strftime('%d/%m/%Y %H:%M') if reference.heure_fin_planifie else None,
                "peut_bouger": _peut_bouger(reference),
            },
            "travaux_en_conflit": [{
                "id": str(t.id),
                "planning_nom": t.planning.nom,
                "ressource": _nom_ressource(t),
                "segment": t.segment,
                "priorite": t.priorite,
                "debut": t.heure_debut_planifie.strftime('%d/%m/%Y %H:%M'),
                "fin": t.heure_fin_planifie.strftime('%d/%m/%Y %H:%M'),
                "peut_bouger": _peut_bouger(t),
            } for t in autres]
        })

        for travail in autres:
            type_travail = travail.type_travaux.libelle if travail.type_travaux else ""

            if not _peut_bouger(travail):
                proposition = PropositionAlignement.objects.create(
                    planning=travail.planning,
                    travail_a_modifier=travail,
                    travail_reference=reference,
                    type_proposition=(
                        PropositionAlignement.TypeProposition.ALIGNEMENT_TRANSPORT
                        if reference.segment == 'TRANSPORT'
                        else PropositionAlignement.TypeProposition.ALIGNEMENT_TRAVAUX
                    ),
                    type_travaux_reference=type_ref,
                    type_travaux_a_modifier=type_travail,
                    priorite_travail=travail.priorite or '',
                    ancien_debut=travail.heure_debut_planifie,
                    ancienne_fin=travail.heure_fin_planifie,
                    nouveau_debut=travail.heure_debut_planifie,
                    nouvelle_fin=travail.heure_fin_planifie,
                    raison=(
                        f"Travail '{_nom_ressource(travail)}' ({travail.segment} - "
                        f"{travail.priorite}) ne peut pas être déplacé. "
                        f"Conflit avec '{_nom_ressource(reference)}' "
                        f"(planning : {reference.planning.nom}). "
                        f"Résolution manuelle requise."
                    ),
                    statut=PropositionAlignement.Statut.BLOQUEE,
                    cree_par=user
                )
                propositions_creees.append(proposition)
                nb_bloquees += 1
                continue

            nouveau_debut, nouvelle_fin = _calculer_nouvel_horaire(travail, reference)
            disponible, detail_conflit = _charge_disponible(
                travail.charge_consignation,
                nouveau_debut, nouvelle_fin,
                exclure_id=travail.id
            )

            raison = (
                f"Chevauchement sur {_nom_ressource(reference)}. "
                f"Période analysée : {periode}. "
                f"Référence : '{_nom_ressource(reference)}' "
                f"(planning : {reference.planning.nom}, {reference.segment}) "
                f"de {reference.heure_debut_planifie.strftime('%d/%m %H:%M') if reference.heure_debut_planifie else None} "
                f"à {reference.heure_fin_planifie.strftime('%d/%m %H:%M')if reference.heure_fin_planifie else None}. "
                f"Proposition : {travail.heure_debut_planifie.strftime('%d/%m %H:%M')} "
                f"→ {nouveau_debut.strftime('%d/%m %H:%M')}."
            )
            if not disponible:
                raison += f" ⚠️ CONFLIT CHARGE : {detail_conflit}"

            statut_final = (
                PropositionAlignement.Statut.BLOQUEE
                if not disponible
                else PropositionAlignement.Statut.EN_ATTENTE
            )
            if not disponible:
                nb_bloquees += 1

            proposition = PropositionAlignement.objects.create(
                planning=travail.planning,
                travail_a_modifier=travail,
                travail_reference=reference,
                type_proposition=(
                    PropositionAlignement.TypeProposition.ALIGNEMENT_TRANSPORT
                    if reference.segment == 'TRANSPORT'
                    else PropositionAlignement.TypeProposition.ALIGNEMENT_TRAVAUX
                ),
                type_travaux_reference=type_ref,
                type_travaux_a_modifier=type_travail,
                priorite_travail=travail.priorite or '',
                ancien_debut=travail.heure_debut_planifie,
                ancienne_fin=travail.heure_fin_planifie,
                nouveau_debut=nouveau_debut,
                nouvelle_fin=nouvelle_fin,
                raison=raison,
                conflit_charge_consignation=not disponible,
                detail_conflit=detail_conflit,
                statut=statut_final,
                cree_par=user
            )
            propositions_creees.append(proposition)

    nb_libres = len(propositions_creees) - nb_bloquees

    return {
        "message": (
            f"{nb_travaux} travaux analysés sur {periode}. "
            f"{len(groupes)} chevauchement(s) détecté(s). "
            f"{len(propositions_creees)} proposition(s) : "
            f"{nb_libres} libre(s), {nb_bloquees} bloquée(s)."
        ),
        "periode": periode,
        "chevauchements": chevauchements_detectes,
        "propositions": propositions_creees,
        "resume": {
            "periode": periode,
            "total_travaux_analyses": nb_travaux,
            "total_chevauchements": len(groupes),
            "total_propositions": len(propositions_creees),
            "propositions_bloquees": nb_bloquees,
            "propositions_libres": nb_libres,
        }
    }