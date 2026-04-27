from django.db import models

from django.db import models
from pilotage.models import Workflow, WorkflowStep
from user.models import Utilisateur
from referentiel.models import ReferenceReseau
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

class PlanningTravaux(models.Model):

    STATUT_TRAVAUX = [
        ('BROUILLON', 'Brouillon'),
        ('SOUMIS', 'Soumis'),
        ('VALIDE', 'Validé'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('REPORTE', 'Reporté')
    ]
    
    id = models.UUIDField(_('id'), default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    titre = models.CharField(max_length=255)
    reference = models.ForeignKey(ReferenceReseau, on_delete=models.PROTECT)
    type_activite = models.ForeignKey(TypeActivite, on_delete=models.PROTECT)
    cree_par = models.ForeignKey( Utilisateur, on_delete=models.PROTECT, related_name="travaux_crees")
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name="travaux_modifies")
    workflow = models.ForeignKey(Workflow, on_delete=models.SET_NULL, null=True, related_name="plannings")
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name="current_plannings")
    
    jour_debut_planifie = models.DateField()
    jour_debut_effectif = models.DateField(null=True, blank=True)

    duree_planifiee = models.PositiveIntegerField(help_text="Durée en jours")
    jour_fin_planifie = models.DateField()

    observation = models.TextField(blank=True)
    statut_travaux = models.CharField(max_length=20, choices=STATUT_TRAVAUX)

    statut_probleme = models.BooleanField(default=False)
    probleme_rencontre = models.TextField(blank=True)

    travail_en_alignement = models.BooleanField(default=False)
    date_report_travaux = models.DateField(null=True, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre
    
    class Meta:
        ordering = ['date_creation']
