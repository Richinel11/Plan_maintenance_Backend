from rest_framework import serializers
from .models import Planning, Travail, TypeActivite
from user.models import Utilisateur, EntiteMetier
from referentiel.models import Centrale, Ouvrage, Troncon, Depart, Poste
from referentiel.serializers import OuvrageSerializer, DepartSerializer, TronconSerializer, PosteSerializer
from pilotage.serializers import WorkflowStepSerializer, WorkflowShortSerializer
from pilotage.models import WorkflowStep, Workflow


class TypeActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeActivite
        fields = ['id', 'libelle']


class UtilisateurShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'first_name', 'last_name']


class CentraleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centrale
        fields = ['id', 'nom', 'capacite_mw']


class EntiteMetierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntiteMetier
        fields = ['id', 'name']


# ─────────────────────────────────────────────
#  Planning
# ─────────────────────────────────────────────

class PlanningSerializer(serializers.ModelSerializer):

    # READ
    entite_metier = EntiteMetierShortSerializer(read_only=True)
    workflow = WorkflowShortSerializer(read_only=True)
    current_step = WorkflowStepSerializer(read_only=True)
    cree_par = UtilisateurShortSerializer(read_only=True)
    modifie_par = UtilisateurShortSerializer(read_only=True)

    # WRITE
    entite_metier_id = serializers.PrimaryKeyRelatedField(
        queryset=EntiteMetier.objects.all(), source='entite_metier',
        write_only=True, allow_null=True, required=False
    )
    workflow_id = serializers.PrimaryKeyRelatedField(
        queryset=Workflow.objects.all(), source='workflow',
        write_only=True, allow_null=True, required=False
    )
    current_step_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowStep.objects.all(), source='current_step',
        write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Planning
        fields = [
            'id', 'nom', 'code',
            'date_creation', 'date_modification',
            # READ
            'entite_metier', 'workflow', 'current_step',
            'cree_par', 'modifie_par',
            # WRITE
            'entite_metier_id', 'workflow_id', 'current_step_id',
        ]
        read_only_fields = ['code', 'date_creation', 'date_modification']


# ─────────────────────────────────────────────
#  Travail
# ─────────────────────────────────────────────

class TravailSerializer(serializers.ModelSerializer):

    # READ
    planning = PlanningSerializer(read_only=True)
    type_travaux = TypeActiviteSerializer(read_only=True)
    cree_par = UtilisateurShortSerializer(read_only=True)
    modifie_par = UtilisateurShortSerializer(read_only=True)
    entite_metier = EntiteMetierShortSerializer(read_only=True)
    ouvrage = OuvrageSerializer(read_only=True)
    poste = PosteSerializer(read_only=True)
    depart = DepartSerializer(read_only=True)
    troncon = TronconSerializer(read_only=True)
    charge_consignation = UtilisateurShortSerializer(read_only=True)
    centrale_thermique_sollicitee = CentraleSerializer(read_only=True)

    # WRITE
    planning_id = serializers.PrimaryKeyRelatedField(
        queryset=Planning.objects.all(), source='planning', write_only=True
    )
    type_travaux_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeActivite.objects.all(), source='type_travaux',
        write_only=True, allow_null=True, required=False
    )
    entite_metier_id = serializers.PrimaryKeyRelatedField(
        queryset=EntiteMetier.objects.all(), source='entite_metier',
        write_only=True, allow_null=True, required=False
    )
    ouvrage_id = serializers.PrimaryKeyRelatedField(
        queryset=Ouvrage.objects.all(), source='ouvrage',
        write_only=True, allow_null=True, required=False
    )
    poste_id = serializers.PrimaryKeyRelatedField(
        queryset=Poste.objects.all(), source='poste',
        write_only=True, allow_null=True, required=False
    )
    depart_id = serializers.PrimaryKeyRelatedField(
        queryset=Depart.objects.all(), source='depart',
        write_only=True, allow_null=True, required=False
    )
    troncon_id = serializers.PrimaryKeyRelatedField(
        queryset=Troncon.objects.all(), source='troncon',
        write_only=True, allow_null=True, required=False
    )
    charge_consignation_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.filter(user_roles__role__code_role="CHARGE_CONSIGNATION").distinct(),
        source='charge_consignation', write_only=True, allow_null=True, required=False
    )
    centrale_thermique_sollicitee_id = serializers.PrimaryKeyRelatedField(
        queryset=Centrale.objects.all(), source='centrale_thermique_sollicitee',
        write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Travail
        fields = [
            'id', 'segment', 'reference', 'statut_travaux',
            'consistance_travaux', 'observations',
            'type_reseau', 'troncons_consignes', 'localites_impactees', 'moyens_mis_en_oeuvre',

            # Programmation temporelle
            'heure_debut_planifie', 'duree', 'unite_duree',
            'heure_fin_planifie',
            'date_programmee',
            'nombre_jours_avant_travaux',

            # Indicateurs PRODUCTION
            'disponibilite_mecanique_mw', 'prevision_puissance_sollicitee',
            'prevision_puissance_interrompue', 'qte_fuel_sollicitee', 'prevision_enf_mwh',

            # Statut
            'statut_probleme', 'probleme_rencontre', 'travail_en_alignement', 'date_report_travaux',

            # Audit
            'date_creation', 'date_modification',

            # READ
            'planning', 'type_travaux', 'cree_par', 'modifie_par',
            'entite_metier', 'ouvrage', 'poste', 'depart',
            'troncon', 'charge_consignation', 'centrale_thermique_sollicitee',

            # WRITE
            'planning_id', 'type_travaux_id', 'entite_metier_id',
            'ouvrage_id', 'poste_id', 'depart_id', 'troncon_id',
            'charge_consignation_id', 'centrale_thermique_sollicitee_id',
        ]
        read_only_fields = ['reference', 'heure_fin_planifie', 'nombre_jours_avant_travaux',
                            'prevision_enf_mwh', 'date_creation', 'date_modification']
