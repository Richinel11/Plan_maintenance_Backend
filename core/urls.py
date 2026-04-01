
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls'), name= 'user' ),
    path('exploitation/', include('exploitation.urls'), name= 'exploitation' ),
    path('pilotage/', include('pilotage.urls'), name= 'pilotage' ),
    path('planning/', include('planning.urls'), name= 'planning' ),
    path('referentiel/', include('referentiel.urls'), name= 'referentiel' ),


] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
