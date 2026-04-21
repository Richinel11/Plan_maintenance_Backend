from django.db import models
from dropdownlist import TaskType , Reference ,RequestingUnit,ThermalPower,NetworkTypes,Troncons, TaskType , Consignmentcharges ,Segments , Ouvrages , Poste , Depart
from user import Utilisateur
import uuid

from dropdownlist import TaskType

class Travail(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    reference = models.CharField(max_length=255)
    segments = models.ForeignKey(Segments, on_delete=models.CASCADE)
    ouvrage = models.ForeignKey(Ouvrages , on_delete=models.CASCADE)
    poste = models.ForeignKey(Poste , on_delete=models.CASCADE)
    depart = models.ForeignKey(Depart, on_delete=models.CASCADE) #depart
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE) #type de travail
    requesting_unit = models.ForeignKey(RequestingUnit, on_delete=models.CASCADE) #unite demanderesse
    localite = models.CharField(max_length=255) 
    network_types = models.ForeignKey(NetworkTypes, on_delete=models.CASCADE) #type de reseau
    troncons= models.ForeignKey(Troncons, on_delete=models.CASCADE) # localitee impacteeelete=models.CASCADE) # consigne de charge
    Mechanical_availability = models.CharField(max_length=255) #disponibilite mecanique
    Consistency_work = models.CharField(max_length=255) #consistance du travail
    Resources_deployed = models.CharField(max_length=255) # moyens mis en oeuvre
    observations = models.TextField(max_length=500)

    # programmation temporelle
    heure_debut_planifier = models.TimeField() # heure de debut planifie
    Duree = models.DurationField() # heure de debut planifie
    heure_fin_planifier = models.TimeField() # date de fin planifie  
    date_programmer= models.DateField() # date de programmation
    nbre_jour_avant_travaux = models.DurationField() 

    #audits
    date_creation = models.DateTimeField(auto_now_add=True) # date de creation
    date_modification = models.DateTimeField(auto_now=True) # date de modification
    Id_user_createur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name="travaux_crees") # utilisateur createur
    Id_user_modificateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name="travaux_modifies") # utilisateur modificateur

    #indicateur d'impact
    thermal_power = models.ForeignKey(ThermalPower, on_delete=models.CASCADE) #centrale thermique solicite
    Puissance_sollicite = models.IntegerField()
    puissance_interrompu = models.IntegerField()
    previsio_ENF = models.IntegerField() #prevision ENF
    Qte_flux_sollicite = models.IntegerField()
     


