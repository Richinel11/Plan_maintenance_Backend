from django.db import models
from pilotage.models import Workflow, WorkflowStep
from user.models import Utilisateur, EntiteMetier
from referentiel.models import Reference
from django.utils.translation import gettext as _
import uuid


class TypeActivite(models.Model):
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    libelle = models.CharField(max_length=100)
    entite_metier = models.ForeignKey('user.EntiteMetier', on_delete=models.PROTECT, null=True, blank=True, related_name='types_activite')
    date_creation = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.libelle

    class Meta:
        ordering = ['libelle']


class Planning(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True, blank=True)
    entite_metier = models.ForeignKey(EntiteMetier, on_delete=models.PROTECT, null=True, blank=True, related_name='plannings')
    workflow = models.ForeignKey(Workflow, on_delete=models.SET_NULL, null=True, blank=True)
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, blank=True)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='plannings_crees')
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='plannings_modifies', null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        from django.utils import timezone
        now = timezone.now()
        prefix = f"PLAN-{now.strftime('%Y%m')}"
        
        # On cherche le dernier code généré pour ce mois pour incrémenter correctement
        last_planning = Planning.objects.filter(code__startswith=prefix).order_by('code').last()
        
        if last_planning:
            try:
                # On extrait le numéro à la fin du code (ex: 0005 de PLAN-202405-0005)
                last_number = int(last_planning.code.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                # Si le format est imprévu, on se rabat sur le count pour éviter de bloquer
                new_number = Planning.objects.filter(code__startswith=prefix).count() + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"

    def __str__(self):
        return f"{self.code} - {self.nom}"

    class Meta:
        ordering = ['-date_creation']


class Travail(models.Model):

    class Segment(models.TextChoices):
        DISTRIBUTION = "DISTRIBUTION", _("Distribution")
        TRANSPORT    = "TRANSPORT",    _("Transport")
        PRODUCTION   = "PRODUCTION",   _("Production")
        
    class Priorite(models.TextChoices):
        P1 = "P1", _("P1 - Urgent")
        P2 = "P2", _("P2 - Non urgent 1 à 7 jours")
        P3 = "P3", _("P3 -  Non urgent 7 jours")

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
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE, related_name='travaux')

    #  Identification
    segment = models.CharField(max_length=20, choices=Segment.choices)
    priorite = models.CharField(
        max_length=5,
        choices=Priorite.choices,
        default=Priorite.P3,
        null=True, blank=True
    )
    reference = models.ForeignKey(Reference, on_delete=models.SET_NULL, null=True, blank=True, related_name='travaux')

    #  Détails organisationnels
    entite_metier = models.ForeignKey(EntiteMetier, on_delete=models.PROTECT, null=True, blank=True, related_name='travaux')
    unite_demanderesse = models.ForeignKey('user.UniteDemanderesse', on_delete=models.SET_NULL, null=True, blank=True, related_name='travaux')
    type_travaux = models.ForeignKey(TypeActivite, on_delete=models.PROTECT, null=True, blank=True)
    type_reseau = models.CharField(max_length=10, choices=TypeReseau.choices, null=True, blank=True)
    consistance_travaux = models.TextField(blank=True)

    #  Localisation & Consistance (DISTRIBUTION)
    troncons_consignes = models.TextField(blank=True)
    localites_impactees = models.CharField(max_length=255, blank=True)
    moyens_mis_en_oeuvre = models.TextField(blank=True)

    #  Charges de consignation (DISTRIBUTION + TRANSPORT)
    charge_consignation = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    #  Programmation Temporelle
    heure_debut_planifie = models.DateTimeField(null=True, blank=True)
    duree = models.PositiveIntegerField(null=True, blank=True)
    unite_duree = models.CharField(max_length=10, choices=UniteDuree.choices, default=UniteDuree.HEURES)
    heure_fin_planifie = models.DateTimeField(null=True, blank=True)
    date_programmee = models.DateField(null=True, blank=True)
    nombre_jours_avant_travaux = models.IntegerField(null=True, blank=True)

    #  Indicateurs d'Impact (PRODUCTION)
    disponibilite_mecanique_mw = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prevision_puissance_sollicitee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prevision_puissance_interrompue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prevision_enf_mwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    centrale_thermique_sollicitee = models.ForeignKey('referentiel.Centrale', on_delete=models.SET_NULL, null=True, blank=True)
    qte_fuel_sollicitee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)

    #  Statut
    statut_travaux = models.CharField(max_length=20, choices=STATUT_TRAVAUX, default='BROUILLON')
    statut_probleme = models.BooleanField(default=False)
    probleme_rencontre = models.TextField(blank=True)
    travail_en_alignement = models.BooleanField(default=False)
    date_report_travaux = models.DateField(null=True, blank=True)

    #  Audit
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='travaux_crees')
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='travaux_modifies', null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.heure_debut_planifie and self.duree:
            from datetime import timedelta
            if self.unite_duree == 'HEURES':
                self.heure_fin_planifie = self.heure_debut_planifie + timedelta(hours=self.duree)
            else:
                self.heure_fin_planifie = self.heure_debut_planifie + timedelta(days=self.duree)

        if self.date_programmee and self.heure_debut_planifie:
            self.nombre_jours_avant_travaux = (
                self.heure_debut_planifie.date() - self.date_programmee
            ).days

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference.valeur if self.reference else str(self.id)

    class Meta:
        ordering = ['-date_creation']


class PropositionAlignement(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", _("En attente")
        ACCEPTEE   = "ACCEPTEE",   _("Acceptée")
        REFUSEE    = "REFUSEE",    _("Refusée")
        BLOQUEE    = "BLOQUEE",    _("Bloquée - Conflit charge consignation")

    class TypeProposition(models.TextChoices):
        ALIGNEMENT_TRANSPORT = "ALIGNEMENT_TRANSPORT", _("Alignement sur transport")
        ALIGNEMENT_TRAVAUX   = "ALIGNEMENT_TRAVAUX",   _("Alignement entre travaux")

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    # Le planning concerné par la proposition
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE,related_name='propositions')

    # Le travail qu'on propose de modifier
    travail_a_modifier = models.ForeignKey(Travail, on_delete=models.CASCADE,related_name='propositions_modification')

    # Le travail de référence (celui sur lequel on aligne)
    travail_reference = models.ForeignKey(Travail, on_delete=models.CASCADE,related_name='propositions_reference',null=True, blank=True)

    type_proposition = models.CharField(max_length=30, choices=TypeProposition.choices)

    # Infos sur les types de travaux pour aider le gestionnaire
    type_travaux_reference = models.CharField(max_length=100, blank=True)
    type_travaux_a_modifier = models.CharField(max_length=100, blank=True)
    priorite_travail = models.CharField(max_length=5, blank=True)

    # Anciens horaires
    ancien_debut = models.DateTimeField()
    ancienne_fin = models.DateTimeField(null=True, blank=True)

    # Nouveaux horaires proposés
    nouveau_debut = models.DateTimeField()
    nouvelle_fin = models.DateTimeField(null=True, blank=True)

    # Raison et notes
    raison = models.TextField(blank=True)
    note_compatibilite_types = models.TextField(blank=True)

    # Conflit charge de consignation
    conflit_charge_consignation = models.BooleanField(default=False)
    detail_conflit = models.TextField(blank=True)

    statut = models.CharField(max_length=20, choices=Statut.choices,default=Statut.EN_ATTENTE)

    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL,null=True, related_name='propositions_creees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proposition {self.type_proposition} - {self.travail_a_modifier}"

    class Meta:
        ordering = ['-created_at']