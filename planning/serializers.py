from rest_framework import serializers
from .models import PlanningTravaux, TypeActivite, ChargeConsignation
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
        fields = ['id', 'nom', 'type', 'capacite_mw']


class ChargeConsignationSerializer(serializers.Serializer):
    class Meta :
        model = ChargeConsignation
        fields = ['id','nom', 'prenom', 'matricule']


class EntiteMetierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntiteMetier
        fields = ['id', 'nom']



class PlanningTravauxSerializer(serializers.ModelSerializer):

    # ── READ ──
    type_travaux = TypeActiviteSerializer(read_only=True)
    cree_par = UtilisateurShortSerializer(read_only=True)
    modifie_par = UtilisateurShortSerializer(read_only=True)
    unite_demanderesse = EntiteMetierShortSerializer(read_only=True)
    ouvrage = OuvrageSerializer(read_only=True)
    poste = PosteSerializer(read_only=True)
    depart = DepartSerializer(read_only=True)
    troncon = TronconSerializer(read_only=True)
    charge_consignation = ChargeConsignationSerializer(read_only=True)
    centrale_thermique_sollicitee = CentraleSerializer(read_only=True)
    workflow = WorkflowShortSerializer(read_only=True)
    current_step = WorkflowStepSerializer(read_only=True)

    # ── WRITE ──
    type_travaux_id = serializers.PrimaryKeyRelatedField(queryset=TypeActivite.objects.all(), source='type_travaux',write_only=True, allow_null=True, required=False)
    cree_par_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all(), source='cree_par',write_only=True)
    modifie_par_id = serializers.PrimaryKeyRelatedField(queryset=Utilisateur.objects.all(), source='modifie_par',write_only=True)
    unite_demanderesse_id = serializers.PrimaryKeyRelatedField(
        queryset=EntiteMetier.objects.all(), source='unite_demanderesse',
        write_only=True, allow_null=True, required=False)
    ouvrage_id = serializers.PrimaryKeyRelatedField(
        queryset=Ouvrage.objects.all(), source='ouvrage',
        write_only=True, allow_null=True, required=False)
    poste_id = serializers.PrimaryKeyRelatedField(
        queryset=Poste.objects.all(), source='poste',
        write_only=True, allow_null=True, required=False)
    depart_id = serializers.PrimaryKeyRelatedField(
        queryset=Depart.objects.all(), source='depart',
        write_only=True, allow_null=True, required=False)   
    troncon_id = serializers.PrimaryKeyRelatedField(
        queryset=Troncon.objects.all(), source='troncon',
        write_only=True, allow_null=True, required=False)
    charge_consignation_id = serializers.PrimaryKeyRelatedField(
        queryset=ChargeConsignation.objects.all(), source='charge_consignation',
        write_only=True, allow_null=True, required=False)
    centrale_thermique_sollicitee_id = serializers.PrimaryKeyRelatedField(
        queryset=Centrale.objects.all(), source='centrale_thermique_sollicitee',
        write_only=True, allow_null=True, required=False)
    workflow_id = serializers.PrimaryKeyRelatedField(
        queryset=Workflow.objects.all(), source='workflow',
        write_only=True, allow_null=True, required=False)
    current_step_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowStep.objects.all(), source='current_step',
        write_only=True, allow_null=True, required=False)

    class Meta:
        model = PlanningTravaux
        fields = [
            'id', 'segment', 'reference', 'statut_travaux','consistance_travaux', 'observations',
            'type_reseau', 'troncons_consignes','localites_impactees', 'moyens_mis_en_oeuvre',

            # Programmation temporelle
            'heure_debut_planifie', 'duree', 'unite_duree',
            'heure_fin_planifie',           # calculé auto
            'date_programmee',
            'nombre_jours_avant_travaux',   # calculé auto

            # Indicateurs PRODUCTION
            'disponibilite_mecanique_mw','prevision_puissance_sollicitee','prevision_puissance_interrompue',
            'qte_fuel_sollicitee',
            'prevision_enf_mwh',            # calculé auto
            
            # Statut
            'statut_probleme', 'probleme_rencontre','travail_en_alignement', 'date_report_travaux',

            # Audit
            'date_creation', 'date_modification',

            # READ
            'type_travaux', 'cree_par', 'modifie_par','unite_demanderesse', 'ouvrage', 'poste','depart', 
            'troncon', 'charge_consignation','centrale_thermique_sollicitee','workflow', 'current_step',

            # WRITE
            'type_travaux_id', 'cree_par_id', 'modifie_par_id','unite_demanderesse_id', 'ouvrage_id', 'poste_id','depart_id', 
            'troncon_id', 'charge_consignation_id','centrale_thermique_sollicitee_id','workflow_id', 'current_step_id',
        ]