from django.urls import path, include
from .views import descargar_modelos, index,pagina_de_carga, retroalimentar_video, estadisticas_view
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('', index, name='index'),
    path('pagina_de_carga/', pagina_de_carga, name='pagina_de_carga'),
    path('retroalimentar_video/', retroalimentar_video, name='retroalimentar_video'),
    path('estadisticas/', estadisticas_view, name='estadisticas'), 
    path('descargar-modelos/', descargar_modelos, name='descargar_modelos'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)