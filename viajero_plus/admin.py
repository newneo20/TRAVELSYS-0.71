from django.contrib import admin
from backoffice.models import Hotel, Habitacion, Oferta

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('hotel_nombre', 'proveedor', 'categoria')
    search_fields = ('hotel_nombre', 'direccion')

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'tipo')
    search_fields = ('hotel__hotel_nombre', 'tipo')

@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'tipo_habitacion', 'temporada', 'sencilla', 'doble', 'triple')
    search_fields = ('hotel__hotel_nombre', 'tipo_habitacion', 'temporada')
