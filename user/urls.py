
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginAPIView, LogoutAPIView, EntiteMetierViewSet,create_user, get_users, get_update_user, delete_user, restore_user

router = DefaultRouter()
router.register(r'entites', EntiteMetierViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('users/all-users', get_users, name="get-all-users"),
    path('users/find-user/<uuid:user_id>',get_update_user, name='user'),
    path('users/create-user',create_user, name='create-user'),
    path('users/delete-user/<uuid:user_id>',delete_user, name='delete-user'),
    path('users/update-user/<uuid:user_id>',get_update_user, name='update-user'),
    path('users/patch-user/<uuid:user_id>',get_update_user, name='modify-user'),
    path('users/restore-user/<uuid:user_id>',restore_user, name='restore-user'),

    path("login/", LoginAPIView.as_view(), name='login'),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
]

