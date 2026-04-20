from django.db import models
from django.contrib.auth import get_user_model
from user.models import EntiteMetier
from referentiel.models import ReferenceReseau
from planning.models import TypeActivite
from exploitation.models import DemandeRetrait, NoteArret

User = get_user_model()

class PilotageTravail(models.Model):
    # Identification du travail
    
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Responsables du travail
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="travaux_pilotage")
    entite = models.ForeignKey(EntiteMetier, on_delete=models.SET_NULL, null=True, related_name="travaux_pilotage")

    # Référentiel
    reference_reseau = models.ForeignKey(ReferenceReseau, on_delete=models.SET_NULL, null=True, blank=True)
    type_activite = models.ForeignKey(TypeActivite, on_delete=models.SET_NULL, null=True, blank=True)

    # Planning 
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=[
        ("BROUILLON", "Brouillon"),
        ("SOUMIS", "Soumis"),
        ("VALIDE", "Validé"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("REPORTE", "Reporté"),
        ("ANNULE", "Annulé")
    ], default="BROUILLON")
    
    travail_en_alignement = models.BooleanField(default=False)

    # Workflow
    current_step = models.CharField(max_length=50, default="creation")  # étape du workflow

    # Exploitation
    demande_retrait = models.OneToOneField(DemandeRetrait, on_delete=models.SET_NULL, null=True, blank=True)
    note_arret = models.OneToOneField(NoteArret, on_delete=models.SET_NULL, null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre
    
class Transition (models.Model):
    from_state = models.CharField(max_length=10)
    to_state = models.CharField(max_length=10)
    