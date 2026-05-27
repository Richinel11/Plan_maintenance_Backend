
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  

router = DefaultRouter()
router.register(r'entites', views.EntiteMetierViewSet)
router.register(r'unites-demanderesses', views.UniteDemanderesseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('create-user',views.create_user, name='create-user'),
    path('all-users', views.get_users, name="get-all-users"),
    
    path('find-user/<uuid:user_id>/',views.find_user, name='find_user'),
    path('change-password/', views.change_password, name = 'change_password'),
    path('charges-consignation/', views.get_charges_consignation, name='get-charges-consignation'),
    path('delete-user/<uuid:user_id>',views.delete_user, name='delete-user'),
    path('update-user/<uuid:user_id>',views.get_update_user, name='update-user'),
    path('patch-user/<uuid:user_id>',views.get_update_user, name='modify-user'),
    path('restore-user/<uuid:user_id>',views.restore_user, name='restore-user'),

    path("login/", views.LoginAPIView.as_view(), name='login'),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
]

