# viajero_plus/urls.py

from django.contrib import admin # type: ignore
from django.urls import path, include # type: ignore
from django.views.generic import TemplateView # type: ignore
from django.conf import settings # type: ignore # Importa las configuraciones
from django.conf.urls.static import static # type: ignore # Importa para servir media y estáticos

app_name = 'backoffice'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('backoffice/', include('backoffice.urls', namespace='backoffice')),  # Incluye el namespace aquí
    path('booking/', include('booking.urls', namespace='booking')),
    
    path('finanzas/', include('finanzas.urls')),
    
    path('renta_hoteles/', include('renta_hoteles.urls')),
    path('renta_autos/', include('renta_autos.urls')),
    path('vuelos/', include('vuelos.urls')),
    path('gestion_economica/', include('gestion_economica.urls')),

    # Rutas de la API (si aplica)
    path('api/', include('booking.urls', namespace='booking_api')),  # Asignamos un namespace único aquí

    # Página principal
    path('', TemplateView.as_view(template_name='index.html')),
]

# Configuración para servir archivos media y estáticos durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
