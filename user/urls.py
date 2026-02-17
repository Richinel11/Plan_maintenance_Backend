
from django.urls import path
from .views import login_view, logout_view, set_password_view, dashboard_view,users_view,user_create,change_user_status_view, get_user_info, update_user_view

app_name = "user"

urlpatterns = [
    # Views
    path("", login_view, name="login"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("set-password/", set_password_view, name="set-password"),
    path("logout/", logout_view, name="logout"),
    path("users", users_view, name="users"),
    
    # Functions
    path("user-create", user_create, name="user-create"), #create a new user
    path("users/<uuid:user_id>/toggle-status/", change_user_status_view, name="toggle-user-status"), #change user status
    path("users/<uuid:user_id>/get-info/", get_user_info, name="get-user-info"), # Fetch user info
    path("users/<uuid:user_id>/update/", update_user_view, name="update-user"), # Update user
]
