from rest_framework import serializers
from .models import Planning, Travail, TypeActivite, PropositionAlignement
from user.models import Utilisateur, EntiteMetier
from referentiel.models import Centrale, Reference
from referentiel.serializers import CentraleSerializer, ReferenceSerializer
from user.models import UniteDemanderesse
from user.serializers import UniteDemanderesseSerializer
from pilotage.serializers import WorkflowStepSerializer, WorkflowShortSerializer
from pilotage.models import WorkflowStep, Workflow


class UtilisateurShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'first_name', 'last_name']


class EntiteMetierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntiteMetier
        fields = ['id', 'name']


class TypeActiviteSerializer(serializers.ModelSerializer):
    entite_metier = EntiteMetierShortSerializer(read_only=True)
    entite_metier_id = serializers.PrimaryKeyRelatedField(
        queryset=EntiteMetier.objects.all(), source='entite_metier',
        write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = TypeActivite
        fields = ['id', 'libelle', 'entite_metier', 'entite_metier_id']


#  Planning

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


#  Travail

class TravailSerializer(serializers.ModelSerializer):

    # READ
    planning = PlanningSerializer(read_only=True)
    type_travaux = TypeActiviteSerializer(read_only=True)
    cree_par = UtilisateurShortSerializer(read_only=True)
    modifie_par = UtilisateurShortSerializer(read_only=True)
    entite_metier = EntiteMetierShortSerializer(read_only=True)
    unite_demanderesse = UniteDemanderesseSerializer(read_only=True)
    reference = ReferenceSerializer(read_only=True)
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
    unite_demanderesse_id = serializers.PrimaryKeyRelatedField(
        queryset=UniteDemanderesse.objects.all(), source='unite_demanderesse',
        write_only=True, allow_null=True, required=False
    )
    reference_id = serializers.PrimaryKeyRelatedField(
        queryset=Reference.objects.all(), source='reference',
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
            'id', 'segment', 'statut_travaux',
            'consistance_travaux', 'observations',
            'type_reseau', 'troncons_consignes', 'localites_impactees', 'moyens_mis_en_oeuvre',

            # Programmation temporelle
            'heure_debut_planifie', 'duree', 'unite_duree',
            'heure_fin_planifie', 'date_programmee', 'nombre_jours_avant_travaux',

            # Indicateurs PRODUCTION
            'disponibilite_mecanique_mw', 'prevision_puissance_sollicitee',
            'prevision_puissance_interrompue', 'qte_fuel_sollicitee', 'prevision_enf_mwh',

            # Statut
            'statut_probleme', 'probleme_rencontre', 'travail_en_alignement', 'date_report_travaux',

            # Audit
            'date_creation', 'date_modification',

            # READ
            'planning', 'type_travaux', 'cree_par', 'modifie_par',
            'entite_metier', 'unite_demanderesse', 'reference',
            'charge_consignation', 'centrale_thermique_sollicitee',

            # WRITE
            'planning_id', 'type_travaux_id', 'entite_metier_id',
            'unite_demanderesse_id', 'reference_id',
            'charge_consignation_id', 'centrale_thermique_sollicitee_id',
        ]
        read_only_fields = ['heure_fin_planifie', 'nombre_jours_avant_travaux',
                            'prevision_enf_mwh', 'date_creation', 'date_modification']


class PropositionAlignementSerializer(serializers.ModelSerializer):
    
    travail_a_modifier_ref = serializers.SerializerMethodField()
    travail_reference_ref = serializers.SerializerMethodField()
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    
    class Meta:
        model = PropositionAlignement
        
        fields = [
             'id', 'type_proposition', 'statut',
            'priorite_travail','type_travaux_reference',
            'type_travaux_a_modifier',
            'note_compatibilite_types','ancien_debut',
            'ancienne_fin','nouveau_debut', 'nouvelle_fin',
            'raison','conflit_charge_consignation',
            'detail_conflit','travail_a_modifier',
            'travail_a_modifier_ref','travail_reference',
            'travail_reference_ref','cree_par_nom', 'created_at'
        ]
        
        
    def get_travail_a_modifier_ref(self, obj):
        if obj.travail_a_modifier and obj.travail_a_modifier.reference:
            return obj.travail_a_modifier.reference.valeur
        return str(obj.travail_a_modifier.id) 
    
    
    def get_travail_reference_ref(self, obj):
        if obj.travail_reference and obj.travail_reference.reference:
            return obj.travail_reference.reference.valeur
        return str(obj.travail_reference.id) if obj.travail_reference else None
    