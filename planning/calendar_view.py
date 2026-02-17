from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import PlanningTravaux, TypeActivite


def calendar_view(request): 
    plannings = PlanningTravaux.objects.all()

    tasks = []
    for p in plannings:
        tasks.append({
            "id": str(p.id),
            "name": p.titre,
            "start": p.jour_debut_planifie.strftime("%Y-%m-%d"),
            "end": p.jour_fin_planifie.strftime("%Y-%m-%d"),
            "progress": 100 if p.statut_travaux == "SOUMIS" else 50,
            "custom_class": p.statut_travaux.lower(),
        })

    context = {
        "tasks": tasks,
        'page_title': 'Vue Planning Calendrier'
    }
    return render(request, "calendar_view.html",context)

