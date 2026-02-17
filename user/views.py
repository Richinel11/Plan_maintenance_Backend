from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from .validators.LoginForm import LoginForm
from django.contrib import messages
from utils import LDAP_connect 
from .models import Utilisateur,Role,EntiteMetier
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404

# Create your views here.
@csrf_exempt
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Veuillez renseigner tous les champs.")
            return redirect("/")
        
        try:
            user = Utilisateur.objects.select_related("role", "entite_metier").get(
                username=username,
                actif=True
            )
        except Utilisateur.DoesNotExist:
            messages.error(request, "Utilisateur non autorisé.")
            return redirect("/")
        
        # --- Dual Authentication Logic ---
        if user.ldap_req:
            # LDAP Authentication
            try:
                user_info = LDAP_connect.ldap_login(username, password)
                # If simplified, user_info might just be dict. 
                # Assuming LDAP_connect returns valid info on success.
                ldap_dn = user_info.get("dn")
                ldap_groups = user_info.get("groups", [])
            except Exception as e:
                messages.error(request, str(e))
                return redirect("/")
        else:
            # Local Authentication
            if not check_password(password, user.password):
                messages.error(request, "Mot de passe incorrect.")
                return redirect("/")
            
            # Check First Connection
            if user.first_connection:
                request.session["pending_user_id"] = str(user.id)
                return redirect("user:set-password")

            # Local users might not have LDAP info
            ldap_dn = ""
            ldap_groups = []

        # --- Session Setup ---
        request.session["user_id"] = str(user.id)
        request.session["username"] = user.username
        request.session["nom"] = user.nom
        request.session["prenom"] = user.prenom
        request.session["role"] = user.role.nom
        request.session["entite"] = user.entite_metier.nom
        request.session["ldap_dn"] = ldap_dn
        request.session["ldap_groups"] = ldap_groups

        request.session.set_expiry(60 * 60 * 6)  # 6 heures
        
        return redirect("user:dashboard")

    return render(request, "auth/login.html")


def logout_view(request):
    request.session.flush()
    return redirect("/")



def set_password_view(request):
    pending_user_id = request.session.get("pending_user_id")
    if not pending_user_id:
        return redirect("/")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "auth/set_password.html")
        
        try:
            user = Utilisateur.objects.get(id=pending_user_id)
            user.password = make_password(new_password)
            user.first_connection = False
            user.save()

            # Clear pending and log user in automatically
            del request.session["pending_user_id"]
            
            # Re-fetch or reuse user data for session
            request.session["user_id"] = str(user.id)
            request.session["username"] = user.username
            request.session["nom"] = user.nom
            request.session["prenom"] = user.prenom
            request.session["role"] = user.role.nom
            request.session["entite"] = user.entite_metier.nom
            request.session.set_expiry(60 * 60 * 6)

            messages.success(request, "Mot de passe mis à jour avec succès.")
            return redirect("user:dashboard")

        except Utilisateur.DoesNotExist:
            return redirect("/")

    return render(request, "auth/set_password.html")


def dashboard_view(request):
    if not request.session.get("user_id"):
        return redirect("/")
    return render(request, "dashboard/dashboard.html")

# Create a new user
def users_view(request):
    if not request.session.get("user_id"):
        return redirect("/")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        users = Utilisateur.objects.select_related("role").order_by("-date_creation")

        data = []
        for user in users:
            data.append({
                "id": user.id, 
                "utilisateur": f"""
                    <div class="user-cell">
                        <img class="avatar" src="/static/images/profile_img.png">
                        <div>
                            <strong>{user.prenom} {user.nom}</strong><br/>
                            <small>#{user.username}</small>
                        </div>
                    </div>
                """,
                "email": user.email or "—",
                "role": user.role.nom if user.role else "",
                "statut": (
                    '<span class="status active">Active</span>'
                    if user.actif else
                    '<span class="status inactive">Inactive</span>'
                ),
                "date_creation": user.date_creation.strftime("%b. %d, %Y"),
                "actions": f"""
                    <div class="action-buttons">
                        <button class="btn-toggle-status"
                                data-id="{user.id}"
                                data-actif="{str(user.actif).lower()}">
                            {"Désactiver" if user.actif else "Activer"}
                        </button>

                        <button class="btn-edit"
                                data-id="{user.id}">
                            Éditer
                        </button>
                    </div>
                """
            })

        return JsonResponse({"data": data})

    roles = Role.objects.all()
    return render(request, "users/users.html", {
        "page_title": "Utilisateurs",
        "roles": roles
    })

# Change user status
@require_POST
def change_user_status_view(request, user_id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Fetch user FIRST
    user = get_object_or_404(Utilisateur, id=user_id)

    # Prevent self-deactivation
    if str(request.session.get("user_id")) == str(user.id):
        return JsonResponse(
            {"error": "You cannot deactivate yourself"},
            status=400
        )

    # Toggle status
    user.actif = not user.actif
    user.save(update_fields=["actif"])

    statut_html = (
        '<span class="status active">Active</span>'
        if user.actif else
        '<span class="status inactive">Inactive</span>'
    )

    actions_html = f"""
        <div class="action-buttons">
            <button class="btn-toggle-status"
                    data-id="{user.id}"
                    data-actif="{str(user.actif).lower()}">
                {"Désactiver" if user.actif else "Activer"}
            </button>

            <button class="btn-edit"
                    data-id="{user.id}">
                Éditer
            </button>
        </div>
    """

    return JsonResponse({
        "success": True,
        "statut_html": statut_html,
        "actions_html": actions_html,
        "actif": user.actif
    })

# Get a specified user
@require_GET
def get_user_info(request, user_id):
    """
    Returns user info as JSON for the edit modal
    """
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user = get_object_or_404(Utilisateur, id=user_id)

    return JsonResponse({
        "id": str(user.id),
        "nom": user.nom,
        "prenom": user.prenom,
        "username": user.username,
        "email": user.email or "",
        "role": str(user.role.id)
    })


# Update a user
@require_POST
def update_user_view(request, user_id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user = get_object_or_404(Utilisateur, id=user_id)

    nom = request.POST.get("nom")
    prenom = request.POST.get("prenom")
    username = request.POST.get("username")
    email = request.POST.get("email")
    role_id = request.POST.get("role")

    if not all([nom, prenom, username, role_id]):
        return JsonResponse({"error": "Tous les champs requis ne sont pas remplis."}, status=400)

    # Update user
    user.nom = nom
    user.prenom = prenom
    user.username = username
    user.email = email
    user.role_id = role_id
    user.save()

    # Prepare HTML snippets
    username_html = f""" 
            <div class="user-cell">
                <img class="avatar" src="/static/images/profile_img.png">
                <div>
                    <strong>{user.prenom} {user.nom}</strong><br/>
                    <small>#{user.username}</small>
                </div>
            </div>        
        """

    statut_html = (
        '<span class="status active">Active</span>'
        if user.actif else
        '<span class="status inactive">Inactive</span>'
    )

    actions_html = f"""
        <div class="action-buttons">
            <button class="btn-toggle-status"
                    data-id="{user.id}"
                    data-actif="{str(user.actif).lower()}">
                {"Désactiver" if user.actif else "Activer"}
            </button>

            <button class="btn-edit"
                    data-id="{user.id}">
                Éditer
            </button>
        </div>
    """

    # Return **all fields needed by DataTable**
    return JsonResponse({
        "success": True,
        "utilisateur":username_html,
        "email": user.email or "—",
        "role": user.role.nom,
        "statut_html": statut_html,
        "date_creation": user.date_creation.strftime("%Y-%m-%d %H:%M"),
        "actions_html": actions_html
    })



def user_create(request):
    if request.method == "POST":
        role = Role.objects.get(id=request.POST.get("role"))
        metier = EntiteMetier.objects.get(id = 'aa7e74ff-f325-4c30-b3de-96ebef304d33')
        user = Utilisateur.objects.create(
            prenom=request.POST.get("prenom"),
            nom=request.POST.get("nom"),
            username=request.POST.get("username"),
            email=request.POST.get("email"),
            role=role,
            entite_metier=metier,
            actif=False
        )

        return JsonResponse({"success": True})