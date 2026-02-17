from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import PlanningTravaux, TypeActivite


# Create your views here.
def planning_view(request):
    if not request.session.get("user_id"):
        return redirect("/")
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        plannings = PlanningTravaux.objects.order_by("-date_creation")

        data = []
        for plan in plannings:
            data.append({
                "id": plan.id, 
                "titre": plan.titre or "—",
                "reference": plan.reference.code_reference or "—",
                "type_activite": (
                    '<span class="status active">Maintenance</span>'
                    if plan.type_activite.libelle == "Maintenance" else
                    '<span class="status inactive">Urgence</span>'
                ),
                "jour_debut_planifie": plan.jour_debut_planifie or "—",
                "jour_debut_effectif": plan.jour_debut_effectif or "—",
                "duree_planifiee": plan.duree_planifiee or "—",
                "jour_fin_planifie": plan.jour_fin_planifie or "—",
                "observation": plan.observation or "—",
                "statut_travaux": plan.statut_travaux or "—",
                "statut_probleme": plan.statut_probleme or "—",
                "probleme_rencontre": plan.probleme_rencontre or "—",
                "travail_en_alignement": plan.travail_en_alignement or "—",
                "date_report_travaux": plan.date_report_travaux or "—",
                "cree_par": plan.cree_par.username or "—",
                "modifie_par": plan.modifie_par.username or "—",
                "date_modification": plan.date_modification.strftime("%b. %d, %Y") or "—",
                "date_creation": plan.date_creation.strftime("%b. %d, %Y"),
               
            })

        return JsonResponse({"data": data})
    return render(request, "planning_view.html",{
        'page_title': 'Plannings'
    })
    
    