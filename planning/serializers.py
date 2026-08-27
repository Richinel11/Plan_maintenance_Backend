from datetime import timedelta
from rest_framework import serializers
from .models import Planning, Travail, TypeActivite, PropositionAlignement
from .alignement_service import _charge_disponible
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
    class Meta:
        model = Planning
        fields = [
            'id', 'nom', 'code', 'transmis_au_responsable', 'date_transmission',
            'date_creation', 'date_modification',
            # READ
            'entite_metier', 'workflow', 'current_step',
            'cree_par', 'modifie_par',
            # WRITE
            'entite_metier_id',
        ]
        read_only_fields = ['code', 'date_creation', 'date_modification', 'transmis_au_responsable', 'date_transmission']


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
    # Relations inverses OneToOne (DDR / NAPT) — nécessaires pour l'affichage
    # du verrou DDR et du bouton "Terminer" (NAPT diffusée) côté frontend.
    demande_retrait = serializers.SerializerMethodField()
    note_arret = serializers.SerializerMethodField()

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
            'id', 'segment','priorite', 'statut_travaux',
            'consistance_travaux', 'observations',
            'type_reseau', 'troncons_consignes', 'localites_impactees', 'moyens_mis_en_oeuvre',

            # Programmation temporelle
            'heure_debut_planifie', 'duree', 'unite_duree',
            'heure_fin_planifie', 'date_programmee', 'nombre_jours_avant_travaux',
             #  Nouveaux champs
             'type_alignement',   # calculé automatiquement (read-only)
             'niveau_coupure',     # rempli par l'utilisateur pour DISTRIBUTION

            # Indicateurs PRODUCTION
            'disponibilite_mecanique_mw', 'prevision_puissance_sollicitee',
            'prevision_puissance_interrompue', 'qte_fuel_sollicitee', 'prevision_enf_mwh',

            # Statut
            'statut_probleme', 'probleme_rencontre', 'travail_en_alignement',
            'alignement_verrouille', 'date_report_travaux',

            # Audit
            'date_creation', 'date_modification',

            # READ
            'planning', 'type_travaux', 'cree_par', 'modifie_par',
            'entite_metier', 'unite_demanderesse', 'reference',
            'charge_consignation', 'centrale_thermique_sollicitee',
            'demande_retrait', 'note_arret',

            # WRITE
            'planning_id', 'type_travaux_id', 'entite_metier_id',
            'unite_demanderesse_id', 'reference_id',
            'charge_consignation_id', 'centrale_thermique_sollicitee_id',
        ]
        read_only_fields = [
            'heure_fin_planifie', 'nombre_jours_avant_travaux',
            'prevision_enf_mwh', 'date_creation', 'date_modification',
            'type_alignement'   #  calculé automatiquement
            ]

    def get_demande_retrait(self, obj):
        ddr = getattr(obj, 'demande_retrait', None)
        if not ddr:
            return None
        return {
            'id': str(ddr.id),
            'reference': ddr.reference,
            'statut': ddr.statut,
        }

    def get_note_arret(self, obj):
        napt = getattr(obj, 'note_arret', None)
        if not napt:
            return None
        return {
            'id': str(napt.id),
            'reference': napt.reference,
            'numero_NAPT': napt.numero_NAPT,
            'statut': napt.statut,
        }

    def validate(self, attrs):
        segment = attrs.get('segment')
        
        if segment == 'DISTRIBUTION':
            # niveau_coupure recommandé pour que l'alignement fonctionne bien
            pass 
        
        elif segment == 'TRANSPORT':
            #charge_consignation fortement recommandé
            if not attrs.get('charge_consignation'):
                raise serializers.ValidationError({
                    "charge_consignation": "Requis pour le segment TRANSPORT."
                })
                
        elif segment == 'PRODUCTION':
            # disponnibilite_mecanique_mw requis
            if not attrs.get('disponibilite_mecanique_mw'):
                raise serializers.ValidationError({
                    "disponibilite_mecanique_mw": "Requis pour le segment PRODUCTION."
                })

        self._valider_disponibilite_charge(attrs)
        return attrs

    def _valider_disponibilite_charge(self, attrs):
        """
        Vérifie que le chargé de consignation n'est pas déjà occupé sur le
        nouveau créneau quand début ET durée sont fournis ensemble (c'est le
        cas de l'écran de réajustement manuel, qui ne passe pas par le
        système de propositions et n'a donc jamais cette vérification —
        cf. alignement_service._charge_disponible / analyser_mois).
        Ignoré si le PATCH ne touche pas les deux à la fois (mise à jour
        partielle d'un autre champ) : pas assez d'information pour recalculer
        la nouvelle fenêtre.
        """
        debut = attrs.get('heure_debut_planifie')
        duree = attrs.get('duree')
        if not debut or not duree:
            return

        charge = attrs.get(
            'charge_consignation',
            self.instance.charge_consignation if self.instance else None
        )
        if not charge:
            return

        unite = attrs.get(
            'unite_duree',
            self.instance.unite_duree if self.instance else 'HEURES'
        )
        if unite == 'JOURS':
            fin = debut + timedelta(days=duree)
        elif unite == 'SEMAINES':
            fin = debut + timedelta(weeks=duree)
        else:
            fin = debut + timedelta(hours=duree)

        exclure_id = self.instance.id if self.instance else None
        disponible, detail = _charge_disponible(charge, debut, fin, exclure_id=exclure_id)
        if not disponible:
            raise serializers.ValidationError({
                "charge_consignation": f"Chargé de consignation indisponible sur ce créneau : {detail}"
            })
    
    


class PropositionAlignementSerializer(serializers.ModelSerializer):

    travail_a_modifier_ref = serializers.SerializerMethodField()
    travail_reference_ref = serializers.SerializerMethodField()
    travail_a_modifier_verrouille = serializers.BooleanField(
        source='travail_a_modifier.alignement_verrouille', read_only=True
    )
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    planning = serializers.SerializerMethodField()

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
            'travail_a_modifier_ref','travail_a_modifier_verrouille',
            'travail_reference',
            'travail_reference_ref','cree_par_nom', 'created_at',
            'planning',
        ]


    def get_travail_a_modifier_ref(self, obj):
        if obj.travail_a_modifier and obj.travail_a_modifier.reference:
            return obj.travail_a_modifier.reference.valeur
        return str(obj.travail_a_modifier.id)

    def get_travail_reference_ref(self, obj):
        if obj.travail_reference and obj.travail_reference.reference:
            return obj.travail_reference.reference.valeur
        return str(obj.travail_reference.id) if obj.travail_reference else None

    def get_planning(self, obj):
        if obj.travail_a_modifier and obj.travail_a_modifier.planning_id:
            return str(obj.travail_a_modifier.planning_id)
        return None
    
