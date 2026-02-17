from django.urls import path
from .views import planning_view
from .calendar_view import calendar_view
app_name = "planning"

urlpatterns = [
    path("planning", planning_view , name="planning"),
    path("calendar", calendar_view, name="calendar"),
    # path("calendar", '', name="login"),
    # path("", login_view, name="login"),
]
