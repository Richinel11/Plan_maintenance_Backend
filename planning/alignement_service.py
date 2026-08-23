from django.utils import timezone
import calendar
from datetime import timedelta, datetime
from .models import Travail, PropositionAlignement


# HELPERS DE BASE

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

# Valeurs tolérées pour chaque niveau de coupure : le modèle Travail.NiveauCoupure
# déclare POSTES/DEPARTS (pluriel) mais des lignes existantes en base utilisent
# encore l'ancien singulier POSTE/DEPART (CharField choices non imposé en BDD).
NIVEAU_COUPURE_POSTE = ('POSTE', 'POSTES')
NIVEAU_COUPURE_DEPART = ('DEPART', 'DEPARTS')

def _est_coupure_au_poste(travail: Travail) -> bool:
    """travaux transport coupe toujours au niveau du poste, quel que soit le champ niveau_coupure."""
    if travail.segment == 'TRANSPORT':
        return True
    return travail.niveau_coupure in NIVEAU_COUPURE_POSTE # type: ignore[attr-defined]



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
    if coupure_a == 'RAME' and coupure_b in NIVEAU_COUPURE_DEPART:
        return bool(rame_a) and rame_a == rame_b
    if coupure_b == 'RAME' and coupure_a in NIVEAU_COUPURE_DEPART:
        return bool(rame_b) and rame_a == rame_b

    # cas 3 : coupure départ → compatible si même départ
    if coupure_a in NIVEAU_COUPURE_DEPART and coupure_b in NIVEAU_COUPURE_DEPART:
        return bool(depart_a) and depart_a == depart_b
    
    return False 

 # PRIORITÉ
PRIORITE_ORDRE = {'TRANSPORT': 0, 'VERROUILLE': 1, 'P1': 2, 'P2': 3, 'P3': 4, None: 5}


def _peut_bouger(travail: Travail) -> bool:
    """
    Règle métier :
    - TRANSPORT → ne bouge JAMAIS
    - Alignement verrouillé par un gestionnaire → ne bouge plus (décision
      manuelle définitive, cf. Travail.alignement_verrouille)
    - P1 → ne bouge pas (urgent)
    - P2, P3 → peut bouger
    """
    if travail.segment == 'TRANSPORT':
        return False
    if travail.alignement_verrouille: # type: ignore[attr-defined]
        return False
    if travail.priorite == 'P1': # type: ignore[attr-defined]
        return False
    return True

def _raison_non_deplacable(travail: Travail) -> str:
    """Explique pourquoi un travail non déplaçable ne bouge pas (cf. _peut_bouger)."""
    if travail.alignement_verrouille: # type: ignore[attr-defined]
        return "son alignement a été fixé manuellement par un gestionnaire"
    if travail.segment == 'TRANSPORT':
        return "un travail TRANSPORT ne bouge jamais"
    return f"priorité {travail.priorite} (urgent)"

def _score_priorite(travail: Travail) -> int:
    """
    Retourne un score numérique pour la priorité d'un travail, plus bas = plus prioritaire.
    Un alignement verrouillé manuellement passe juste après TRANSPORT : c'est
    une décision humaine délibérée, elle doit devenir la référence du groupe
    (les autres s'alignent sur elle) plutôt que l'inverse.
    """
    if travail.segment == 'TRANSPORT':
        return PRIORITE_ORDRE['TRANSPORT']
    if travail.alignement_verrouille: # type: ignore[attr-defined]
        return PRIORITE_ORDRE['VERROUILLE']
    return PRIORITE_ORDRE.get(travail.priorite, 5) #type: ignore[attr-defined]

# CHARGE DE CONSIGNATION
def _charge_disponible(charge, nouveau_debut, nouvelle_fin, exclure_id=None, alignements_proposes=None) -> tuple:
    """
    Vérifie si le charge de consignation est libre sur la nouvelle période.

    Logique :
    - On cherche tous ses autres travaux déjà enregistrés en base
    - On vérifie aussi les alignements déjà décidés plus tôt DANS CETTE MÊME
      analyse (alignements_proposes) : deux travaux d'un même groupe qui
      partagent le même chargé de consignation et sont tous les deux calés
      sur la fenêtre du pivot n'apparaissent pas comme en conflit l'un avec
      l'autre en base (aucun des deux n'a encore été réellement déplacé,
      seule une proposition existe) — sans ce second passage, les deux
      propositions ressortiraient EN_ATTENTE alors que les appliquer toutes
      les deux double-réserverait la même personne sur le même créneau.
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

    for alignement in (alignements_proposes or []):
        if alignement['charge_id'] != charge.id or alignement['travail_id'] == exclure_id:
            continue
        if _periodes_se_chevauchent(nouveau_debut, nouvelle_fin,
                                    alignement['debut'], alignement['fin']):
            return False, (
                f"{charge.get_full_name()} est déjà proposé sur le travail "
                f"'{alignement['ressource']}' de {alignement['debut'].strftime('%d/%m %H:%M')} "
                f"à {alignement['fin'].strftime('%d/%m %H:%M')} dans cette même analyse."
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
    
def _invalider_propositions_obsoletes(travaux: list, pairs_valides: set) -> None:
    """
    Referme (statut REFUSEE) toute proposition EN_ATTENTE/BLOQUEE dont le
    couple (travail_a_modifier, travail_reference) ne correspond plus à un
    conflit détecté dans l'analyse en cours.

    Sans ce nettoyage, une proposition dont le conflit a été résolu autrement
    (réajustement manuel, changement de segment/priorité/référence...) reste
    EN_ATTENTE indéfiniment avec des dates devenues obsolètes — au risque
    d'être appliquée plus tard et de recréer un conflit déjà résolu.
    """
    en_cours = PropositionAlignement.objects.filter(
        travail_a_modifier_id__in=[t.id for t in travaux],
        statut__in=[
            PropositionAlignement.Statut.EN_ATTENTE,
            PropositionAlignement.Statut.BLOQUEE,
        ],
    )
    for proposition in en_cours:
        cle = (proposition.travail_a_modifier_id, proposition.travail_reference_id)
        if cle in pairs_valides:
            continue
        proposition.statut = PropositionAlignement.Statut.REFUSEE
        proposition.raison = (
            "[Invalidée automatiquement — conflit résolu autrement] "
            f"{proposition.raison}"
        )
        proposition.save(update_fields=['statut', 'raison', 'updated_at'])


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

    groupes = _detecter_groupes(travaux) if nb_travaux >= 2 else []
    # Pivot calculé une seule fois par groupe (réutilisé pour le nettoyage et
    # pour la génération des propositions plus bas).
    groupes_avec_pivot = [(groupe, _trouver_reference(groupe)) for groupe in groupes]

    # Nettoyage : toute proposition EN_ATTENTE/BLOQUEE dont le couple
    # (travail_a_modifier, travail_reference) ne fait plus partie d'un
    # conflit détecté par cette analyse est refermée (voir
    # _invalider_propositions_obsoletes). Fait avant les retours anticipés
    # pour que le nettoyage ait bien lieu même si plus aucun conflit
    # n'est détecté ce mois-ci.
    if travaux:
        pairs_valides = {
            (t.id, reference.id)
            for groupe, reference in groupes_avec_pivot
            for t in groupe if t.id != reference.id
        }
        _invalider_propositions_obsoletes(travaux, pairs_valides)

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

    # Propositions actives déjà existantes pour ces travaux : on les réutilise
    # au lieu d'en recréer, pour ne pas dupliquer en base à chaque nouvel
    # appel de l'analyse (rechargement de page, clic "Analyser"...).
    # Seuls EN_ATTENTE/BLOQUEE sont réutilisés : une proposition terminale
    # (ACCEPTEE/REFUSEE) ne doit jamais bloquer la régénération d'une
    # proposition fraîche si le même couple redevient conflictuel plus tard.
    propositions_existantes = {
        (p.travail_a_modifier_id, p.travail_reference_id): p
        for p in PropositionAlignement.objects.filter(
            travail_a_modifier_id__in=[t.id for t in travaux],
            statut__in=[
                PropositionAlignement.Statut.EN_ATTENTE,
                PropositionAlignement.Statut.BLOQUEE,
            ],
        )
    }

    # Fenêtres déjà proposées EN_ATTENTE dans cette même analyse (tous
    # groupes confondus) : permet à _charge_disponible de détecter deux
    # travaux d'un même chargé de consignation alignés au même moment sans
    # que ni l'un ni l'autre n'apparaisse encore comme déplacé en base (voir
    # _charge_disponible).
    alignements_proposes = []

    for groupe, reference in groupes_avec_pivot:
        autres = [t for t in groupe if t.id != reference.id]
        type_ref = reference.type_travaux.libelle if reference.type_travaux else "Non défini"

        chevauchements_detectes.append({
            "reference": {
                "id": str(reference.id),
                "planning_id": str(reference.planning_id),
                "planning_nom": reference.planning.nom,
                "ressource": _nom_ressource(reference),
                "segment": reference.segment,
                "priorite": reference.priorite,
                "type_travaux": type_ref,
                "debut": reference.heure_debut_planifie.strftime('%d/%m/%Y %H:%M') if reference.heure_debut_planifie else None,
                "fin": reference.heure_fin_planifie.strftime('%d/%m/%Y %H:%M') if reference.heure_fin_planifie else None,
                "peut_bouger": _peut_bouger(reference),
                "alignement_verrouille": reference.alignement_verrouille,
            },
            "travaux_en_conflit": [{
                "id": str(t.id),
                "planning_id": str(t.planning_id),
                "planning_nom": t.planning.nom,
                "ressource": _nom_ressource(t),
                "segment": t.segment,
                "priorite": t.priorite,
                "debut": t.heure_debut_planifie.strftime('%d/%m/%Y %H:%M'),
                "fin": t.heure_fin_planifie.strftime('%d/%m/%Y %H:%M'),
                "peut_bouger": _peut_bouger(t),
                "alignement_verrouille": t.alignement_verrouille,
            } for t in autres]
        })

        for travail in autres:
            type_travail = travail.type_travaux.libelle if travail.type_travaux else ""
            cle_existante = (travail.id, reference.id)
            proposition_existante = propositions_existantes.get(cle_existante)

            if proposition_existante:
                propositions_creees.append(proposition_existante)
                if proposition_existante.statut == PropositionAlignement.Statut.BLOQUEE:
                    nb_bloquees += 1
                elif travail.charge_consignation_id:
                    alignements_proposes.append({
                        'charge_id': travail.charge_consignation_id,
                        'travail_id': travail.id,
                        'debut': proposition_existante.nouveau_debut,
                        'fin': proposition_existante.nouvelle_fin,
                        'ressource': _nom_ressource(travail),
                    })
                continue

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
                        f"{travail.priorite}) ne peut pas être déplacé : "
                        f"{_raison_non_deplacable(travail)}. "
                        f"Conflit avec '{_nom_ressource(reference)}' "
                        f"(planning : {reference.planning.nom}). "
                        f"Résolution manuelle requise."
                    ),
                    statut=PropositionAlignement.Statut.BLOQUEE,
                    cree_par=user
                )
                propositions_existantes[cle_existante] = proposition
                propositions_creees.append(proposition)
                nb_bloquees += 1
                continue

            nouveau_debut, nouvelle_fin = _calculer_nouvel_horaire(travail, reference)
            compatibilite = _analyser_compatibilite(type_ref, type_travail)
            disponible, detail_conflit = _charge_disponible(
                travail.charge_consignation,
                nouveau_debut, nouvelle_fin,
                exclure_id=travail.id,
                alignements_proposes=alignements_proposes,
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
                raison += f" CONFLIT CHARGE : {detail_conflit}"

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
                note_compatibilite_types=f"[{compatibilite['niveau']}] {compatibilite['note']}",
                conflit_charge_consignation=not disponible,
                detail_conflit=detail_conflit,
                statut=statut_final,
                cree_par=user
            )
            propositions_existantes[cle_existante] = proposition
            propositions_creees.append(proposition)
            if disponible and travail.charge_consignation_id:
                alignements_proposes.append({
                    'charge_id': travail.charge_consignation_id,
                    'travail_id': travail.id,
                    'debut': nouveau_debut,
                    'fin': nouvelle_fin,
                    'ressource': _nom_ressource(travail),
                })

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