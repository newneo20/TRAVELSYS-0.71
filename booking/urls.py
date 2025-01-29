# booking/urls.py
from django.urls import path
from . import views

app_name = 'booking'  # Agrega el namespace aquí

urlpatterns = [
    
    # Páginas "en desarrollo" y "en mantenimiento"
    path('en_desarrollo/', views.en_desarrollo, name='en_desarrollo'),    
    path('en_mantenimiento/', views.en_mantenimiento, name='en_mantenimiento'),
    
    path('check-session/', views.check_session_status, name='check_session'),
    
    
    path('hotel_search/', views.hotel_search, name='hotel_search'),
    #path('hotel_results/', views.hotel_results, name='hotel_resultsNO'),    
    path('hotel_detalle/<int:hotel_id>/', views.hotel_detalle, name='hotel_detalleNO'),    
    path('hotel_pago_reserva/<int:hotel_id>/', views.hotel_pago_reserva, name='hotel_pago_reserva'),
    path('complete_solicitud/<int:hotel_id>/', views.complete_solicitud, name='complete_solicitud'),
    path('car_rental_search/', views.car_rental_search, name='car_rental_search'),
    path('transfers_search/', views.transfers_search, name='transfers_search'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('perfil/', views.perfil_cliente, name='perfil_cliente'),
    
    
    path('hotel/dashboard/', views.hotel_dashboard, name='hotel_dashboard'),
    path('hotel/hotel_results/', views.hotel_results, name='hotel_results'),    
    path('hotel/hotel_detalle/<int:hotel_id>/', views.hotel_detalle, name='hotel_detalle'),   
    path('hotel/hotel_pago_reserva/<int:hotel_id>/', views.hotel_pago_reserva, name='hotel_pago_reserva'), 
    
    # ---------------------------------------- Sección: Reservas ---------------------------------------- #
    
    path('reservas/', views.listar_reservas, name='listar_reservas'),
    path('reservas/detalles_reserva/<int:reserva_id>/', views.detalles_reserva, name='detalles_reserva'),
    path('reservas/<str:estado>/', views.listar_reservas, name='listar_reservas_por_estado'),   
    
    # ---------------------------------------- Sección: Remesas ---------------------------------------- #

    path('remesas/remesas', views.remesas, name='remesas'),
    path('remesas/guardar-remesa/', views.guardar_remesa, name='guardar_remesa'),

    # ---------------------------------------- Sección: Traslados ---------------------------------------- #

    path('traslados_search/', views.traslados_search, name='traslados_search'),
    path('traslados/dashboard/', views.traslado_dashboard, name='traslado_dashboard'),
    path('obtener-destinos/', views.obtener_destinos, name='obtener_destinos'),


    
]
