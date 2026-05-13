from django.shortcuts import render
from .models import Travail


def calendar_view(request):
    travaux = Travail.objects.all().select_related('planning')

    tasks = []
    for t in travaux:
        if t.heure_debut_planifie and t.heure_fin_planifie:
            tasks.append({
                "id": str(t.id),
                "name": t.reference,
                "start": t.heure_debut_planifie.strftime("%Y-%m-%d"),
                "end": t.heure_fin_planifie.strftime("%Y-%m-%d"),
                "progress": 100 if t.statut_travaux == "TERMINE" else 50,
                "custom_class": t.statut_travaux.lower(),
            })

    context = {
        "tasks": tasks,
        'page_title': 'Vue Planning Calendrier'
    }
    return render(request, "calendar_view.html", context)
