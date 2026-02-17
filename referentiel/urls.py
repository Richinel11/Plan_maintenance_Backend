from django.urls import path
from .views import (troncon_view, change_troncon_status_view,
depart_view, change_depart_status_view, network_ref_view, change_ref_reseau_status_view,
change_poste_status_view, poste_view)

app_name = "referentiel"

urlpatterns = [
    # template path
    path("troncons", troncon_view, name="troncons"),
    path("depart", depart_view, name="depart"),
    path("poste", poste_view, name="poste"),
    path("ref_reseau", network_ref_view, name="ref_reseau"),
    


    # Function Path
    path("troncons/<uuid:troncon_id>/toggle-status/", change_troncon_status_view, name="toggle-troncon-status"), #change troncon status
    path("depart/<uuid:depart_id>/toggle-status/", change_depart_status_view, name="toggle-depart-status"), #change depart status
    path("poste/<uuid:poste_id>/toggle-status/", change_poste_status_view, name="toggle-poste-status"), #change poste status
    path("ref/<uuid:ref_id>/toggle-status/", change_ref_reseau_status_view, name="toggle-ref-status"), #change ref reseau status
]
