from django.db import models

from django.db import models
from pilotage.models import Workflow, WorkflowStep
from user.models import Utilisateur, EntiteMetier
from referentiel.models import Ouvrage,Poste,Depart,Troncon
from django.utils.translation import gettext as _
import uuid


class TypeActivite(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    libelle = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.libelle
    class Meta:
        ordering = ['date_creation']
        
        
class ChargeConsignation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    matricule = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    class Meta:
        ordering = ['created_at']


class PlanningTravaux(models.Model):

    class Segment(models.TextChoices):
        DISTRIBUTION = "DISTRIBUTION", _("Distribution")
        TRANSPORT    = "TRANSPORT",    _("Transport")
        PRODUCTION   = "PRODUCTION",   _("Production")

    class TypeReseau(models.TextChoices):
        HTB = "HTB", _("HTB (Haute Tension)")
        HTA = "HTA", _("HTA (Moyenne Tension)")
        BT  = "BT",  _("BT (Basse Tension)")

    class UniteDuree(models.TextChoices):
        HEURES = "HEURES", _("Heures")
        JOURS  = "JOURS",  _("Jours")

    STATUT_TRAVAUX = [
        ('BROUILLON', 'Brouillon'),
        ('SOUMIS', 'Soumis'),
        ('VALIDE', 'Validé'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('REPORTE', 'Reporté')
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    #  Identification 
    segment = models.CharField(max_length=20, choices=Segment.choices)
    reference = models.CharField(max_length=255, unique=True, blank=True)  # auto-générée
    ouvrage = models.ForeignKey(Ouvrage, on_delete=models.PROTECT, null=True, blank=True)
    poste = models.ForeignKey(Poste, on_delete=models.PROTECT, null=True, blank=True)
    depart = models.ForeignKey(Depart, on_delete=models.PROTECT, null=True, blank=True)
    troncon = models.ForeignKey(Troncon, on_delete=models.PROTECT, null=True, blank=True)

    #  Détails organisationnels 
    unite_demanderesse = models.ForeignKey(EntiteMetier, on_delete=models.PROTECT, null=True, blank=True)
    type_travaux = models.ForeignKey(TypeActivite, on_delete=models.PROTECT, null=True, blank=True)
    type_reseau = models.CharField(max_length=10, choices=TypeReseau.choices, null=True, blank=True)  # DISTRIBUTION seulement
    consistance_travaux = models.TextField(blank=True)

    #  Localisation & Consistance (DISTRIBUTION) 
    troncons_consignes = models.TextField(blank=True)
    localites_impactees = models.CharField(max_length=255, blank=True)
    moyens_mis_en_oeuvre = models.TextField(blank=True)

    #  Charges de consignation (DISTRIBUTION + TRANSPORT) 
    charge_consignation = models.ForeignKey(ChargeConsignation, on_delete=models.SET_NULL, null=True, blank=True)

    #  Programmation Temporelle 
    heure_debut_planifie = models.DateTimeField(null=True, blank=True)
    duree = models.PositiveIntegerField(null=True, blank=True)
    unite_duree = models.CharField(max_length=10, choices=UniteDuree.choices,default=UniteDuree.HEURES)
    heure_fin_planifie = models.DateTimeField(null=True, blank=True)        # calculé auto
    date_programmee = models.DateField(null=True, blank=True)
    nombre_jours_avant_travaux = models.PositiveIntegerField(null=True, blank=True)  # calculé auto

    #  Indicateurs d'Impact (PRODUCTION) 
    disponibilite_mecanique_mw = models.DecimalField( max_digits=10, decimal_places=2, null=True, blank=True)
    prevision_puissance_sollicitee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prevision_puissance_interrompue = models.DecimalField( max_digits=10, decimal_places=2, null=True, blank=True)
    prevision_enf_mwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # calculé auto
    centrale_thermique_sollicitee = models.ForeignKey('referentiel.Centrale', on_delete=models.SET_NULL,null=True, blank=True)# PRODUCTION seulement
    qte_fuel_sollicitee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)

    #  Statut 
    statut_travaux = models.CharField( max_length=20, choices=STATUT_TRAVAUX, default='BROUILLON')
    statut_probleme = models.BooleanField(default=False)
    probleme_rencontre = models.TextField(blank=True)
    travail_en_alignement = models.BooleanField(default=False)
    date_report_travaux = models.DateField(null=True, blank=True)

    #  Workflow 
    workflow = models.ForeignKey(Workflow, on_delete=models.SET_NULL,null=True, blank=True)
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL,null=True, blank=True)

    #  Audit 
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name="travaux_crees")
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name="travaux_modifies")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-génération de la référence
        self.reference = self._generate_reference()

        # Auto-calcul heure_fin_planifie
        if self.heure_debut_planifie and self.duree:
            from datetime import timedelta
            if self.unite_duree == 'HEURES':
                self.heure_fin_planifie = self.heure_debut_planifie + timedelta(hours=self.duree)
            else:
                self.heure_fin_planifie = self.heure_debut_planifie + timedelta(days=self.duree)

        # Auto-calcul nombre_jours_avant_travaux
        if self.date_programmee and self.heure_debut_planifie:
            self.nombre_jours_avant_travaux = (
                self.heure_debut_planifie.date() - self.date_programmee
            ).days

        super().save(*args, **kwargs)

    def _generate_reference(self):
        if self.segment == 'DISTRIBUTION':
            parts = [
                self.segment,
                self.troncon.nom if self.troncon else '',
                self.poste.nom if self.poste else '',
                self.depart.nom if self.depart else '',
            ]
        elif self.segment == 'TRANSPORT':
            parts = [
                self.segment,
                self.troncon.nom if self.troncon else '',
                self.ouvrage.nom if self.ouvrage else '',
                self.poste.nom if self.poste else '',
            ]
        elif self.segment == 'PRODUCTION':
            parts = [
                self.segment,
                self.troncon.nom if self.troncon else '',
                self.ouvrage.nom if self.ouvrage else '',
                self.poste.nom if self.poste else '',
            ]
        else:
            parts = []
        return '_'.join(filter(None, parts))

    def __str__(self):
        return f"{self.reference}"

