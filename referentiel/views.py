from django.shortcuts import render,redirect
from .models import Troncon, Localisation,Depart,Ouvrage,Poste,ReferenceReseau
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404

# Create your views here.
def troncon_view(request):
    if not request.session.get("user_id"):
        return redirect("/")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        troncons = Troncon.objects.order_by("-date_creation")

        data = []
        for troncon in troncons:
            data.append({
                "id": troncon.id, 
                "nom": troncon.nom or "—",
                "date_creation": troncon.date_creation.strftime("%b. %d, %Y"),
                "statut": (
                    '<span class="status active">Active</span>'
                    if troncon.actif else
                    '<span class="status inactive">Inactive</span>'
                ),
                "actions": f"""
                    <div class="action-buttons">
                        <button class="btn-toggle-status"
                                data-id="{troncon.id}"
                                data-actif="{str(troncon.actif).lower()}">
                            {"Désactiver" if troncon.actif else "Activer"}
                        </button>

                    </div>
                """
            })

        return JsonResponse({"data": data})
    return render(request, "troncons.html",{
        'page_title': 'Tronçons'
    })


@require_POST
def change_troncon_status_view(request, troncon_id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Fetch troncon FIRST
    troncon = get_object_or_404(Troncon, id=troncon_id)

    # Toggle status
    troncon.actif = not troncon.actif
    troncon.save(update_fields=["actif"])

    statut_html = (
        '<span class="status active">Active</span>'
        if troncon.actif else
        '<span class="status inactive">Inactive</span>'
    )

    actions_html = f"""
        <div class="action-buttons">
            <button class="btn-toggle-status"
                    data-id="{troncon.id}"
                    data-actif="{str(troncon.actif).lower()}">
                {"Désactiver" if troncon.actif else "Activer"}
            </button>
        </div>
    """

    return JsonResponse({
        "success": True,
        "statut_html": statut_html,
        "actions_html": actions_html,
        "actif": troncon.actif
    })


def ouvrage_view(request):
    pass


def depart_view(request):
    if not request.session.get("user_id"):
        return redirect("/")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        departs = Depart.objects.order_by("-date_creation")

        data = []
        for depart in departs:
            data.append({
                "id": depart.id, 
                "nom": depart.nom or "—",
                "date_creation": depart.date_creation.strftime("%b. %d, %Y"),
                "statut": (
                    '<span class="status active">Active</span>'
                    if depart.actif else
                    '<span class="status inactive">Inactive</span>'
                ),
                "actions": f"""
                    <div class="action-buttons">
                        <button class="btn-toggle-status"
                                data-id="{depart.id}"
                                data-actif="{str(depart.actif).lower()}">
                            {"Désactiver" if depart.actif else "Activer"}
                        </button>

                    </div>
                """
            })

        return JsonResponse({"data": data})
    return render(request, "depart.html",{
        'page_title': 'Départ'
    })


@require_POST
def change_depart_status_view(request, depart_id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Fetch troncon FIRST
    depart = get_object_or_404(Depart, id=depart_id)

    # Toggle status
    depart.actif = not depart.actif
    depart.save(update_fields=["actif"])

    statut_html = (
        '<span class="status active">Active</span>'
        if depart.actif else
        '<span class="status inactive">Inactive</span>'
    )

    actions_html = f"""
        <div class="action-buttons">
            <button class="btn-toggle-status"
                    data-id="{depart.id}"
                    data-actif="{str(depart.actif).lower()}">
                {"Désactiver" if depart.actif else "Activer"}
            </button>
        </div>
    """

    return JsonResponse({
        "success": True,
        "statut_html": statut_html,
        "actions_html": actions_html,
        "actif": depart.actif
    })



def poste_view(request):
    if not request.session.get("user_id"):
        return redirect("/")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        postes = Poste.objects.order_by("-date_creation")

        data = []
        for poste in postes:
            data.append({
                "id": poste.id, 
                "nom": poste.nom or "—",
                "date_creation": poste.date_creation.strftime("%b. %d, %Y"),
                "statut": (
                    '<span class="status active">Active</span>'
                    if poste.actif else
                    '<span class="status inactive">Inactive</span>'
                ),
                "actions": f"""
                    <div class="action-buttons">
                        <button class="btn-toggle-status"
                                data-id="{poste.id}"
                                data-actif="{str(poste.actif).lower()}">
                            {"Désactiver" if poste.actif else "Activer"}
                        </button>
                    </div>
                """
            })

        return JsonResponse({"data": data})
    return render(request, "poste.html",{
        'page_title': 'Poste'
    })

@require_POST
def change_poste_status_view(request, poste_id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Fetch troncon first or fail
    poste = get_object_or_404(Poste, id=poste_id)

    # Toggle status
    poste.actif = not poste.actif
    poste.save(update_fields=["actif"])

    statut_html = (
        '<span class="status active">Active</span>'
        if poste.actif else
        '<span class="status inactive">Inactive</span>'
    )

    actions_html = f"""
        <div class="action-buttons">
            <button class="btn-toggle-status"
                    data-id="{poste.id}"
                    data-actif="{str(poste.actif).lower()}">
                {"Désactiver" if poste.actif else "Activer"}
            </button>
        </div>
    """

    return JsonResponse({
        "success": True,
        "statut_html": statut_html,
        "actions_html": actions_html,
        "actif": poste.actif
    })


def network_ref_view(request):
    if not request.session.get("user_id"):
        return redirect("/")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        refs = ReferenceReseau.objects.order_by("-date_creation")

        data = []
        for ref in refs:
            data.append({
                "id": ref.id, 
                "reference": ref.code_reference or "—",
                "libelle": ref.libelle or "—",
                "ouvrage": ref.ouvrage.nom or "—",
                "poste": ref.poste.nom or "—",
                "depart": ref.depart.nom or "—",
                "troncon": ref.troncon.nom or "—",
                "localisation": ref.localisation.ville or "—",
                "date_creation": ref.date_creation.strftime("%b. %d, %Y"),
                "statut": (
                    '<span class="status active">Active</span>'
                    if ref.actif else
                    '<span class="status inactive">Inactive</span>'
                ),
                "actions": f"""
                    <div class="action-buttons">
                        <button class="btn-toggle-status"
                                data-id="{ref.id}"
                                data-actif="{str(ref.actif).lower()}">
                            {"Désactiver" if ref.actif else "Activer"}
                        </button>
                    </div>
                """
            })

        return JsonResponse({"data": data})
    return render(request, "ref_reseau.html",{
        'page_title': 'Référence Reseau'
    })

@require_POST
def change_ref_reseau_status_view(request, ref_id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Fetch troncon FIRST
    ref = get_object_or_404(Poste, id=ref_id)

    # Toggle status
    ref.actif = not ref.actif
    ref.save(update_fields=["actif"])

    statut_html = (
        '<span class="status active">Active</span>'
        if ref.actif else
        '<span class="status inactive">Inactive</span>'
    )

    actions_html = f"""
        <div class="action-buttons">
            <button class="btn-toggle-status"
                    data-id="{ref.id}"
                    data-actif="{str(ref.actif).lower()}">
                {"Désactiver" if ref.actif else "Activer"}
            </button>
        </div>
    """

    return JsonResponse({
        "success": True,
        "statut_html": statut_html,
        "actions_html": actions_html,
        "actif": ref.actif
    })
