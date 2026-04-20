from django.db import models
from dropdownlist import TaskType , Reference ,RequestingUnit,ThermalPower,NetworkTypes,Sections, TaskType , Consignmentcharges ,Segments , Ouvrages , Poste , Depart
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
    thermal_power = models.ForeignKey(ThermalPower, on_delete=models.CASCADE) #centrale thermique solicite
    network_types = models.ForeignKey(NetworkTypes, on_delete=models.CASCADE) #type de reseau
    sections = models.ForeignKey(Sections, on_delete=models.CASCADE) # troncons
    Consignment_charges = models.ForeignKey(Consignmentcharges, on_delete=models.CASCADE) # consigne de charge
    Mechanical_availability = models.CharField(max_length=255) #disponibilite mecanique
    Consistency_work = models.CharField(max_length=255) #consistance du travail
    Resources_deployed = models.CharField(max_length=255) # moyens mis en oeuvre
     


