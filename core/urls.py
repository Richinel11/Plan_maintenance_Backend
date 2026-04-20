
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
   
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls'), name= 'user' ),
    path('', include('exploitation.urls'), name= 'exploitation' ),
    path('', include('pilotage.urls'), name= 'pilotage' ),
    path('', include('planning.urls'), name= 'planning' ),
    path('', include('referentiel.urls'), name= 'referentiel' ),
    path('', include('security.urls'), name='security'),
    
     # Swagger / Spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),


] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
    
    
    
    
