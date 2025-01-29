# usuarios/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import login_view

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', login_view, name='login'),  # Usa tu vista personalizada
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('check-session/', views.check_session_status, name='check_session'),
    
]
