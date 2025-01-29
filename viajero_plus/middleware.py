# viajero_plus/middleware.py
import datetime
from django.conf import settings
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            # Si el usuario no está autenticado, no hacemos nada
            return

        # Obtiene el último tiempo de actividad del usuario
        last_activity = request.session.get('last_activity')
        now = datetime.datetime.now()

        if last_activity:
            # Calcula el tiempo transcurrido desde la última actividad
            elapsed_time = (now - datetime.datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")).seconds
            # Si han pasado más de SESSION_COOKIE_AGE segundos, cerrar la sesión
            if elapsed_time > settings.SESSION_COOKIE_AGE:
                logout(request)
                # Opcional: Puedes redirigir al usuario a la página de inicio de sesión
                return
        
        # Actualiza el último tiempo de actividad
        request.session['last_activity'] = now.strftime("%Y-%m-%d %H:%M:%S")
        


