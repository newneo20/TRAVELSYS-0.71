from pyexpat.errors import messages
from django.forms import model_to_dict # type: ignore
from django.http import HttpResponse # type: ignore

from usuarios.decorators import manager_required # type: ignore
from django.contrib.auth import logout, login, authenticate # type: ignore 
from django.contrib.auth.decorators import login_required # type: ignore

from .models import Hotel, PlanAlimenticio, Proveedor, PoloTuristico, Habitacion, TipoFee, Oferta,HotelFacility,HotelSetting, CadenaHotelera 
from .models import Reserva, Pasajero, HabitacionReserva, OfertasEspeciales, Rentadora, Categoria, ModeloAuto, Location, CertificadoVacaciones
from .models import OpcionCertificado,Servicio, TasaCambio, Traslado, Transportista, Ubicacion, Vehiculo

from django.shortcuts import render, get_object_or_404, redirect # type: ignore
from .forms import PoloTuristicoForm, ProveedorForm, CadenaHoteleraForm, ReservaForm, PasajeroForm, HabitacionForm, OfertasEspecialesForm
from .funciones_externas import combinacion_habitaciones, leer_datos_hoteles
from django.core.serializers import serialize # type: ignore
import json
from django.db.models import Q # type: ignore
from django.http import JsonResponse # type: ignore
import os
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.core.paginator import Paginator # type: ignore
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError, ObjectDoesNotExist # type: ignore
from django.core.files.storage import default_storage # type: ignore
from django.contrib import messages # type: ignore
from django.urls import reverse # type: ignore





@login_required
def check_session_status(request):
    # Si el usuario está autenticado, devuelve "active", de lo contrario "inactive"
    return JsonResponse({'status': 'active'})


# ---------------------------------------- DASHBOARD / PANEL DE CONTROL ----------------------------------------#

@manager_required
@login_required
def dashboard(request):
    return render(request, 'backoffice/dashboard.html')

def en_desarrollo(request):
    return render(request, 'backoffice/en_desarrollo.html')

def en_mantenimiento(request):
    return render(request, 'backoffice/en_mantenimiento.html')

# ---------------------------------------- PROVEEDORES ----------------------------------------#
@manager_required
@login_required
def listar_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'backoffice/proveedores/listar_proveedores.html', {'proveedores': proveedores})

@manager_required
@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        nombre = request.POST.get('nombre')
        correo1 = request.POST.get('correo1')
        correo2 = request.POST.get('correo2')
        correo3 = request.POST.get('correo3')
        telefono = request.POST.get('telefono')
        detalles_cuenta_bancaria = request.POST.get('detalles_cuenta_bancaria')
        direccion = request.POST.get('direccion')
        servicios_ids = request.POST.getlist('servicios')

        # Crear un nuevo proveedor
        nuevo_proveedor = Proveedor(
            nombre=nombre,
            correo1=correo1,
            correo2=correo2,
            correo3=correo3,
            telefono=telefono,
            detalles_cuenta_bancaria=detalles_cuenta_bancaria,
            direccion=direccion
        )
        nuevo_proveedor.save()

        # Asociar los servicios seleccionados
        nuevo_proveedor.servicios.set(servicios_ids)

        return redirect('backoffice:listar_proveedores')

    # Obtener todos los servicios para mostrar en el formulario
    servicios = Servicio.objects.all()
    return render(request, 'backoffice/proveedores/crear_proveedor.html', {'servicios': servicios})

@manager_required
@login_required
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    if request.method == 'POST':
        # Capturar los datos del formulario
        proveedor.nombre = request.POST.get('nombre')
        proveedor.correo1 = request.POST.get('correo1')
        proveedor.correo2 = request.POST.get('correo2')
        proveedor.correo3 = request.POST.get('correo3')
        proveedor.telefono = request.POST.get('telefono')
        proveedor.detalles_cuenta_bancaria = request.POST.get('detalles_cuenta_bancaria')
        proveedor.direccion = request.POST.get('direccion')

        # Actualizar los servicios seleccionados
        servicios_ids = request.POST.getlist('servicios')
        proveedor.servicios.set(servicios_ids)

        # Guardar los cambios
        proveedor.save()
        return redirect('backoffice:listar_proveedores')

    # Obtener todos los servicios para mostrar en el formulario
    servicios = Servicio.objects.all()
    return render(request, 'backoffice/proveedores/editar_proveedor.html', {'proveedor': proveedor, 'servicios': servicios})


@manager_required
@login_required
def eliminar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('backoffice:listar_proveedores')
    return render(request, 'backoffice/proveedores/eliminar_proveedor.html', {'proveedor': proveedor})

# ---------------------------------------- POLOS ---------------------------------------- #
@manager_required
@login_required
def listar_polos(request):
    polos = PoloTuristico.objects.all()
    return render(request, 'backoffice/polos/listar_polos.html', {'polos': polos})

@manager_required
@login_required
def crear_polo_turistico(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        nombre = request.POST.get('nombre')
        pais = request.POST.get('pais')

        # Crear un nuevo PoloTuristico
        nuevo_polo = PoloTuristico(
            nombre=nombre,
            pais=pais,
        )
        nuevo_polo.save()
        return redirect('backoffice:listar_polos')

    return render(request, 'backoffice/polos/crear_polo_turistico.html')

@manager_required
@login_required
def editar_polo_turistico(request, polo_id):
    polo = get_object_or_404(PoloTuristico, id=polo_id)

    if request.method == 'POST':
        # Capturar los datos del formulario
        polo.nombre = request.POST.get('nombre')
        polo.pais = request.POST.get('pais')

        # Guardar los cambios
        polo.save()
        return redirect('backoffice:listar_polos')

    return render(request, 'backoffice/polos/editar_polo_turistico.html', {'polo': polo})


@manager_required
@login_required
def eliminar_polo(request, polo_id):
    polo = get_object_or_404(PoloTuristico, pk=polo_id)
    if request.method == 'POST':
        polo.delete()
        return redirect('backoffice:listar_polos')
    return render(request, 'backoffice/polos/eliminar_polo.html', {'polo': polo})


# ---------------------------------------- HOTELES ---------------------------------------- #

@manager_required
@login_required
def listar_hoteles(request):
    hoteles = Hotel.objects.all()
    query = request.GET.get('q', '')
    if query:
        hoteles = hoteles.filter(
            Q(hotel_nombre__icontains=query) |
            Q(proveedor__nombre__icontains=query) |
            Q(polo_turistico__nombre__icontains=query) |
            Q(cadena_hotelera__nombre__icontains=query)
        )

    paginator = Paginator(hoteles, 10)  # 10 hoteles por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'hoteles': page_obj,
        'query': query,
    }
    return render(request, 'backoffice/hoteles/listar_hoteles.html', context)

@manager_required
@login_required
def hotel_management(request, hotel_id=None):
    # Obtener listas de objetos para los campos de selección.
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()
    proveedores = Proveedor.objects.all()

    # Si se proporciona un `hotel_id`, obtenemos el hotel para editar.
    hotel = get_object_or_404(Hotel, id=hotel_id) if hotel_id else None

    # Obtener habitaciones, configuraciones, ofertas, e instalaciones relacionadas con el hotel.
    habitaciones = Habitacion.objects.filter(hotel_id=hotel_id) if hotel_id else None
    configuraciones = HotelSetting.objects.filter(hotel_id=hotel_id).first() if hotel_id else None
    ofertas = Oferta.objects.filter(hotel_id=hotel_id) if hotel_id else None
    instalaciones = HotelFacility.objects.filter(hotel_id=hotel_id) if hotel_id else None

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'hotel':
            # Crear o actualizar el hotel según la presencia del objeto `hotel`.
            if hotel:
                # Actualizar el hotel existente
                hotel.hotel_nombre = request.POST.get('hotel_nombre')
                hotel.polo_turistico_id = request.POST.get('polo_turistico')
                hotel.cadena_hotelera_id = request.POST.get('cadena_hotelera')
                hotel.proveedor_id = request.POST.get('proveedor')
                hotel.fee = request.POST.get('fee')
                hotel.tipo_fee = request.POST.get('tipo_fee')
                hotel.plan_alimenticio = request.POST.get('plan_alimenticio')
                hotel.descripcion_hotel = request.POST.get('descripcion_hotel')
                hotel.direccion = request.POST.get('direccion')
                hotel.checkin = request.POST.get('checkin')
                hotel.checkout = request.POST.get('checkout')
                hotel.orden = request.POST.get('orden')
                hotel.categoria = request.POST.get('categoria')
                hotel.solo_adultos = 'solo_adultos' in request.POST
                if 'foto_hotel' in request.FILES:
                    hotel.foto_hotel = request.FILES['foto_hotel']
                hotel.save()
                messages.success(request, 'Hotel actualizado correctamente.')
            else:
                # Crear un nuevo hotel
                nuevo_hotel = Hotel(
                    hotel_nombre=request.POST.get('hotel_nombre'),
                    polo_turistico_id=request.POST.get('polo_turistico'),
                    cadena_hotelera_id=request.POST.get('cadena_hotelera'),
                    proveedor_id=request.POST.get('proveedor'),
                    fee=request.POST.get('fee'),
                    tipo_fee=request.POST.get('tipo_fee'),
                    plan_alimenticio=request.POST.get('plan_alimenticio'),
                    descripcion_hotel=request.POST.get('descripcion_hotel'),
                    direccion=request.POST.get('direccion'),
                    checkin=request.POST.get('checkin'),
                    checkout=request.POST.get('checkout'),
                    orden=request.POST.get('orden'),
                    categoria=request.POST.get('categoria'),
                    solo_adultos='solo_adultos' in request.POST,
                    foto_hotel=request.FILES.get('foto_hotel', '')
                )
                nuevo_hotel.save()
                messages.success(request, 'Hotel creado correctamente.')
                return redirect('backoffice:listar_hoteles')

        elif form_type == 'configuraciones':
            # Manejar la configuración del hotel
            if configuraciones:
                configuraciones.edad_limite_nino = request.POST.get('edad_limite_nino', 0)
                configuraciones.edad_limite_infante = request.POST.get('edad_limite_infante', 0)
                configuraciones.cantidad_noches = request.POST.get('cantidad_noches', 0)
                configuraciones.save()
                messages.success(request, 'Configuración actualizada correctamente.')
            else:
                # Crear una nueva configuración si no existe
                HotelSetting.objects.create(
                    hotel=hotel,
                    edad_limite_nino=request.POST.get('edad_limite_nino', 0),
                    edad_limite_infante=request.POST.get('edad_limite_infante', 0),
                    cantidad_noches=request.POST.get('cantidad_noches', 0),
                )
                messages.success(request, 'Configuración creada correctamente.')

        # Otros tipos de formulario como habitaciones, ofertas e instalaciones pueden ser manejados aquí.

        return redirect('backoffice:editar_hotel', hotel_id=hotel.id if hotel else nuevo_hotel.id)

    # Renderizar la plantilla con los datos necesarios para el formulario.
    context = {
        'hotel': hotel,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
        'proveedores': proveedores,
        'habitaciones': habitaciones,
        'configuraciones': configuraciones,
        'ofertas': ofertas,
        'instalaciones': instalaciones,
    }
    return render(request, 'backoffice/hoteles/hotel_management.html', context)

@manager_required
@login_required
def crear_hotel(request):    
    if request.method == 'POST':
        # Obtener los valores del formulario
        hotel_nombre = request.POST.get('hotel_nombre')
        proveedor_id = request.POST.get('proveedor')
        fee = request.POST.get('fee')
        tipo_fee = request.POST.get('tipo_fee')
        polo_turistico_id = request.POST.get('polo_turistico')
        plan_alimenticio = request.POST.get('plan_alimenticio')
        descripcion_hotel = request.POST.get('descripcion_hotel')
        direccion = request.POST.get('direccion')
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        orden = request.POST.get('orden')
        categoria = request.POST.get('categoria')
        cadena_hotelera_id = request.POST.get('cadena_hotelera')
        solo_adultos = request.POST.get('solo_adultos') == 'on'  # Checkboxes return 'on' if checked
        foto_hotel = request.FILES.get('foto_hotel')

        # Crear instancia del hotel
        nuevo_hotel = Hotel(
            hotel_nombre=hotel_nombre,
            proveedor=Proveedor.objects.get(id=proveedor_id) if proveedor_id else None,
            fee=fee,
            tipo_fee=tipo_fee,
            polo_turistico=PoloTuristico.objects.get(id=polo_turistico_id) if polo_turistico_id else None,
            plan_alimenticio=plan_alimenticio,
            descripcion_hotel=descripcion_hotel,
            direccion=direccion,
            checkin=checkin,
            checkout=checkout,
            orden=orden if orden else None,
            categoria=categoria if categoria else None,
            cadena_hotelera=CadenaHotelera.objects.get(id=cadena_hotelera_id) if cadena_hotelera_id else None,
            solo_adultos=solo_adultos,
            foto_hotel=foto_hotel.name if foto_hotel else None
        )

        # Guardar el hotel en la base de datos
        nuevo_hotel.save()

        # Redirigir a una página de éxito o a la lista de hoteles
        return redirect('backoffice:listar_hoteles')

    # Obtener datos para llenar los selects del formulario
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()

    # Renderizar el formulario con los datos
    context = {
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
    }
    return render(request, 'backoffice/hoteles/partials/form_hotel.html', context)

@manager_required
@login_required
def editar_hotel(request, hotel_id):
    # Obtener el hotel por ID o lanzar un error 404 si no existe
    hotel = get_object_or_404(Hotel, id=hotel_id)

    # Obtener listas de proveedores, polos turísticos, y cadenas hoteleras
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()

    # Obtener habitaciones relacionadas con el hotel
    habitaciones = Habitacion.objects.filter(hotel_id=hotel_id)

    # Obtener la configuración relacionada con el hotel (asumiendo que solo hay una por hotel)
    configuraciones = HotelSetting.objects.filter(hotel_id=hotel_id).first()

    # Obtener las ofertas relacionadas con el hotel
    ofertas = Oferta.objects.filter(hotel_id=hotel_id)

    # Obtener las instalaciones relacionadas con el hotel
    instalaciones = HotelFacility.objects.filter(hotel_id=hotel_id)

    if request.method == 'POST' and request.POST.get('form_type') == 'configuraciones':
        # Actualizar la configuración existente
        if configuraciones:
            configuraciones.edad_limite_nino = request.POST.get('edad_limite_nino', 0)
            configuraciones.edad_limite_infante = request.POST.get('edad_limite_infante', 0)
            configuraciones.cantidad_noches = request.POST.get('cantidad_noches', 0)
            configuraciones.save()
            messages.success(request, 'Configuración actualizada correctamente.')
        else:
            # Crear una nueva configuración si no existe
            HotelSetting.objects.create(
                hotel=hotel,
                edad_limite_nino=request.POST.get('edad_limite_nino', 0),
                edad_limite_infante=request.POST.get('edad_limite_infante', 0),
                cantidad_noches=request.POST.get('cantidad_noches', 0),
            )
            messages.success(request, 'Configuración creada correctamente.')

        return redirect('backoffice:editar_hotel', hotel_id=hotel_id)

    # Renderizar el formulario con los datos actuales del hotel
    context = {
        'hotel': hotel,
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
        'habitaciones': habitaciones,
        'configuraciones': configuraciones,
        'ofertas': ofertas,
        'instalaciones': instalaciones,
    }
    return render(request, 'backoffice/hoteles/hotel_management.html', context)

@manager_required
@login_required
def listar_habitaciones(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = Habitacion.objects.filter(hotel=hotel)
    data = {
        'habitaciones': [
            {
                'id': habitacion.id,
                'tipo_habitacion': habitacion.tipo,
                'descripcion': habitacion.descripcion,
                'capacidad_habitacion': habitacion.max_capacidad,
            }
            for habitacion in habitaciones
        ]
    }
    return JsonResponse(data)

# Vista para guardar una nueva habitación
@manager_required
@login_required
def guardar_habitacion(request, hotel_id):
    
    print('*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/')
    print('--- ENTRO A GUARDAR HABITACION ---')
    print('*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/')
    
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        # Obtener los valores del formulario        
        tipo = request.POST.get('tipo', '')
        descripcion = request.POST.get('descripcion', '')
        adultos = request.POST.get('adultos', '0')  # Ajustar el nombre del campo si es necesario
        ninos = request.POST.get('ninos', '0')  # Ajustar el nombre del campo si es necesario
        max_capacidad = request.POST.get('max_capacidad', '0')  # Ajustar el nombre del campo si es necesario
        min_capacidad = request.POST.get('min_capacidad', '0')  # Ajustar el nombre del campo si es necesario
        descripcion_capacidad = request.POST.get('descripcion_capacidad', '')
        admite_3_con_1 = request.POST.get('admite_3_con_1') == 'on'
        solo_adultos = request.POST.get('solo_adultos') == 'on'

        # Convertir valores a los tipos correctos si es necesario
        try:
            adultos = int(adultos)
            ninos = int(ninos)
            max_capacidad = int(max_capacidad)
            min_capacidad = int(min_capacidad)
        except ValueError as e:
            print(f"Error al convertir valores a enteros: {e}")



        # Guardar la habitación
        habitacion = Habitacion(
            hotel=hotel,
            tipo=tipo,
            descripcion=descripcion,
            adultos=adultos,
            ninos=ninos,
            max_capacidad=max_capacidad,
            min_capacidad=min_capacidad,
            descripcion_capacidad=descripcion_capacidad,
            admite_3_con_1=admite_3_con_1,
            solo_adultos=solo_adultos
        )
        habitacion.save()

        return JsonResponse({'success': True, 'message': 'Habitación guardada exitosamente.'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

# Vista para obtener los datos de una habitación específica
def obtener_habitacion_test(request, habitacion_id):
    try:
        habitacion = Habitacion.objects.get(id=habitacion_id)
        data = {
            'habitacion': {
                'id': habitacion.id,
                'tipo': habitacion.tipo,
                'descripcion': habitacion.descripcion,
                'max_capacidad': habitacion.max_capacidad,
                'min_capacidad': habitacion.min_capacidad,
                'adultos': habitacion.adultos,
                'ninos': habitacion.ninos,
                'descripcion_capacidad': habitacion.descripcion_capacidad,
                'admite_3_con_1': habitacion.admite_3_con_1,
                'solo_adultos': habitacion.solo_adultos,
            }
        }
        return JsonResponse(data)
    except Habitacion.DoesNotExist:
        return JsonResponse({'error': 'Habitación no encontrada'}, status=404)


def editar_oferta(request, oferta_id):
    return JsonResponse({'oferta_id': oferta_id})


@csrf_exempt
def crear_editar_oferta(request):

    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            oferta_id = data.get('oferta_id', None)
            
            if oferta_id:
                oferta = Oferta.objects.get(id=oferta_id)
                mensaje = "Oferta actualizada exitosamente."
            else:
                oferta = Oferta()
                mensaje = "Oferta creada exitosamente."

            oferta.disponible = data.get('disponible', False)
            oferta.codigo = data.get('codigo', '')
            oferta.tipo_habitacion = data.get('tipo_habitacion', '')
            oferta.temporada = data.get('temporada', '')
            oferta.booking_window = data.get('booking_window', '')
            oferta.sencilla = data.get('sencilla', '')
            oferta.doble = data.get('doble', '')
            oferta.triple = data.get('triple', '')
            oferta.primer_nino = data.get('primer_nino', '')
            oferta.segundo_nino = data.get('segundo_nino', '')
            oferta.un_adulto_con_ninos = data.get('un_adulto_con_ninos', '')
            oferta.primer_nino_con_un_adulto = data.get('primer_nino_con_un_adulto', '')
            oferta.segundo_nino_con_un_adulto = data.get('segundo_nino_con_un_adulto', '')
            oferta.edad_nino = data.get('edad_nino', '')
            oferta.edad_infante = data.get('edad_infante', '')
            oferta.noches_minimas = data.get('noches_minimas', '')
            oferta.cantidad_habitaciones = data.get('cantidad_habitaciones', 1)
            oferta.tipo_fee = data.get('tipo_fee', '')
            oferta.fee_doble = data.get('fee_doble', '')
            oferta.fee_triple = data.get('fee_triple', '')
            oferta.fee_sencilla = data.get('fee_sencilla', '')
            oferta.fee_primer_nino = data.get('fee_primer_nino', '')
            oferta.fee_segundo_nino = data.get('fee_segundo_nino', '')

            oferta.save()

            return JsonResponse({"status": "success", "message": mensaje})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)



# Vista para editar una habitación existente
@manager_required
@login_required
def editar_habitacion(request, habitacion_id):
    if request.method == 'POST':
        habitacion = get_object_or_404(Habitacion, id=habitacion_id)
        
        habitacion.tipo = request.POST.get('tipo')
        habitacion.descripcion = request.POST.get('descripcion')
        habitacion.adultos = request.POST.get('adultos')
        habitacion.ninos = request.POST.get('ninos',)
        habitacion.max_capacidad = request.POST.get('max_capacidad')
        habitacion.min_capacidad = request.POST.get('min_capacidad')
        habitacion.descripcion_capacidad = request.POST.get('descripcion_capacidad')
        habitacion.admite_3_con_1 = request.POST.get('admite_3_con_1') == 'on'
        habitacion.solo_adultos = request.POST.get('solo_adultos') == 'on'

        
        # Actualiza otros campos
        habitacion.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Vista para eliminar una habitación
@manager_required
@login_required
def eliminar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    habitacion.delete()
    return JsonResponse({'success': True})

@manager_required
@login_required
def hotel_rooms(request):    
    return render(request, 'backoffice/hotel_rooms.html')

@manager_required
@login_required
def hotel_settings(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    setting, created = HotelSetting.objects.get_or_create(hotel=hotel)
    
    context = {
        'setting': setting,
        'hotel': hotel
    }
    return render(request, 'backoffice/hotel_settings.html', context)

@csrf_exempt
@login_required
def guardar_configuracion_hotel(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        setting, created = HotelSetting.objects.get_or_create(hotel=hotel)

        try:
            setting.edad_limite_nino = int(request.POST.get('edadLimite_nino', 0))
            setting.edad_limite_infante = int(request.POST.get('edadLimite_infante', 0))
            setting.cantidad_noches = int(request.POST.get('cantidad_noches', 0))
            setting.save()
            return JsonResponse({'status': 'success'})
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@manager_required
@login_required
def hotel_facilities(request):
    return render(request, 'backoffice/hotel_facilities.html')

@manager_required
@login_required
def hotel_discounts(request):
    return render(request, 'backoffice/hotel_discounts.html')

@manager_required
@login_required
def hotel_tabs(request):
    if request.method == 'POST':
        # Código para manejar la creación del hotel
        hotel_nombre = request.POST.get('hotel_nombre')
        polo_turistico_id = request.POST.get('polo_turistico')
        proveedor_id = request.POST.get('proveedor')
        fee = request.POST.get('fee')
        tipo_fee = request.POST.get('tipo_fee')
        plan_alimenticio = request.POST.get('plan_alimenticio')
        descripcion_hotel = request.POST.get('descripcion_hotel')
        direccion = request.POST.get('direccion')
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        orden = request.POST.get('orden')
        foto_hotel = request.POST.get('foto_hotel')

        # Validar y guardar el hotel
        hotel = Hotel(
            hotel_nombre=hotel_nombre,
            polo_turistico_id=polo_turistico_id,
            proveedor_id=proveedor_id,
            fee=fee,
            tipo_fee=tipo_fee,
            plan_alimenticio=plan_alimenticio,
            descripcion_hotel=descripcion_hotel,
            direccion=direccion,
            checkin=checkin,
            checkout=checkout,
            latitud=latitud,
            longitud=longitud,
            orden=orden,
            foto_hotel=foto_hotel
        )
        hotel.save()
        
        return redirect('hotel_tabs_edit', hotel_id=hotel.id)

    else:
        proveedores = Proveedor.objects.all()
        polos_turisticos = PoloTuristico.objects.all()
        cadenas_hoteleras = CadenaHotelera.objects.all()
        
        context = {
            'proveedores': proveedores,
            'polos_turisticos': polos_turisticos,
            'cadenas_hoteleras' : cadenas_hoteleras,
            'hotel': None  # Ajuste para manejar el hotel_id en la plantilla
        }
        return render(request, 'backoffice/hotel_tabs.html', context)

@manager_required
@login_required
def hotel_tabs_edit(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    if request.method == 'POST':
        # Código para manejar la edición del hotel
        hotel.hotel_nombre = request.POST.get('hotel_nombre')
        hotel.polo_turistico = request.POST.get('polo_turistico')
        hotel.proveedor = request.POST.get('proveedor')
        hotel.fee = request.POST.get('fee')
        hotel.tipo_fee = request.POST.get('tipo_fee')
        hotel.plan_alimenticio = request.POST.get('plan_alimenticio')
        hotel.descripcion_hotel = request.POST.get('descripcion_hotel')
        hotel.direccion = request.POST.get('direccion')
        hotel.checkin = request.POST.get('checkin')
        hotel.checkout = request.POST.get('checkout')
        hotel.latitud = request.POST.get('latitud')
        hotel.longitud = request.POST.get('longitud')
        hotel.orden = request.POST.get('orden')
        hotel.foto_hotel = request.POST.get('foto_hotel')
        hotel.save()
        return redirect('hotel_tabs_edit', hotel_id=hotel.id)
    
    else:
        proveedores = Proveedor.objects.all()
        polos_turisticos = PoloTuristico.objects.all()          
        cadenas_hoteleras = CadenaHotelera.objects.all()
        
        context = {
            'hotel': hotel,
            'proveedores': proveedores,
            'cadenas_hoteleras': cadenas_hoteleras,
            'polos_turisticos': polos_turisticos,
        }
        return render(request, 'backoffice/hotel_tabs_edit.html', context)

@manager_required
@login_required
def hotel_content(request):
    return render(request, 'backoffice/hotel_content.html')

@manager_required
@login_required
def hotel_editar(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    context = {
        'hotel': hotel,
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
    }
    return render(request, 'backoffice/hotel_editar.html', context)

@manager_required
@login_required
def guardar_hotel_editado(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.method == 'POST':
        hotel.hotel_nombre = request.POST.get('hotel_nombre', '')
        hotel.polo_turistico_id = request.POST.get('polo_turistico')
        hotel.cadena_hotelera_id = request.POST.get('cadena_hotelera')
        hotel.proveedor_id = request.POST.get('proveedor')
        hotel.fee = request.POST.get('fee', '')
        hotel.tipo_fee = request.POST.get('tipo_fee', '')
        hotel.plan_alimenticio = request.POST.get('plan_alimenticio', '')
        hotel.descripcion_hotel = request.POST.get('descripcion_hotel', '')
        hotel.direccion = request.POST.get('direccion', '')
        hotel.checkin = request.POST.get('checkin', '')
        hotel.checkout = request.POST.get('checkout', '')
        hotel.orden = request.POST.get('orden', None)
        hotel.categoria = request.POST.get('categoria', None)
        hotel.foto_hotel = request.FILES.get('foto_hotel', None)
        hotel.solo_adultos = 'solo_adultos' in request.POST

        # Guardar el hotel
        hotel.save()

        # Redirigir a la misma página para ver los cambios
        return redirect('backoffice:hotel_tabs_edit', hotel_id=hotel.id)

    # Obtener datos necesarios para el formulario
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()
    proveedores = Proveedor.objects.all()

    context = {
        'hotel': hotel,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
        'proveedores': proveedores,
    }

    return render(request, 'backoffice/hotel_editar.html', context)

@manager_required
@login_required
def guardar_hotel(request):
    if request.method == 'POST':
        hotel_nombre = request.POST.get('hotel_nombre')
        polo_turistico_id = request.POST.get('polo_turistico')
        proveedor_id = request.POST.get('proveedor')
        fee = request.POST.get('fee')
        tipo_fee = request.POST.get('tipo_fee')
        plan_alimenticio = request.POST.get('plan_alimenticio')
        descripcion_hotel = request.POST.get('descripcion_hotel')
        direccion = request.POST.get('direccion')
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        orden = request.POST.get('orden')
        foto_hotel = request.POST.get('foto_hotel')
        categoria = request.POST.get('categoria')

        # Validación manual
        if hotel_nombre and polo_turistico_id and proveedor_id:
            try:
                polo_turistico = PoloTuristico.objects.get(id=polo_turistico_id)
                proveedor = Proveedor.objects.get(id=proveedor_id)

                hotel = Hotel.objects.create(
                    hotel_nombre=hotel_nombre,
                    polo_turistico=polo_turistico,
                    proveedor=proveedor,
                    fee=fee,
                    tipo_fee=tipo_fee,
                    plan_alimenticio=plan_alimenticio,
                    descripcion_hotel=descripcion_hotel,
                    direccion=direccion,
                    checkin=checkin,
                    checkout=checkout,
                    latitud=latitud,
                    longitud=longitud,
                    orden=orden,
                    foto_hotel=foto_hotel,
                    categoria=categoria,
                )
                return redirect('backoffice:hotel_tabs_edit', hotel_id=hotel.id)
            except PoloTuristico.DoesNotExist:
                return HttpResponse('Polo Turístico no existe', status=400)
            except Proveedor.DoesNotExist:
                return HttpResponse('Proveedor no existe', status=400)
        else:
            return HttpResponse('Datos incompletos o inválidos', status=400)
    else:
        return HttpResponse('Método no permitido', status=405)

@manager_required
@login_required
def eliminar_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    if request.method == 'POST':
        hotel.delete()
        return redirect('backoffice:listar_hoteles')
    return render(request, 'backoffice/hoteles/eliminar_hotel.html', {'hotel': hotel})

# ---------------------------------------- CADENAS HOTELERAS ---------------------------------------- #
@manager_required
@login_required
def listar_cadenas_hoteleras(request):
    cadenas_hoteleras_list = CadenaHotelera.objects.all()
    paginator = Paginator(cadenas_hoteleras_list, 5)  # Muestra 10 cadenas hoteleras por página
    
    page_number = request.GET.get('page')
    cadenas_hoteleras = paginator.get_page(page_number)
    
    return render(request, 'backoffice/cadena_hotelera/listar_cadenas_hoteleras.html', {'cadenas_hoteleras': cadenas_hoteleras})

@manager_required
@login_required
def crear_cadena_hotelera(request):
    if request.method == 'POST':
        form = CadenaHoteleraForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_cadenas_hoteleras')
    else:
        form = CadenaHoteleraForm()
    return render(request, 'backoffice/cadena_hotelera/crear_cadena_hotelera.html', {'form': form})

@manager_required
@login_required
def editar_cadena_hotelera(request, pk):
    cadena_hotelera = get_object_or_404(CadenaHotelera, pk=pk)
    if request.method == 'POST':
        form = CadenaHoteleraForm(request.POST, instance=cadena_hotelera)
        if form.is_valid():
            form.save()
            return redirect('listar_cadenas_hoteleras')
    else:
        form = CadenaHoteleraForm(instance=cadena_hotelera)
    return render(request, 'backoffice/cadena_hotelera/editar_cadena_hotelera.html', {'form': form, 'cadena_hotelera': cadena_hotelera})

@manager_required
@login_required
def eliminar_cadena_hotelera(request, pk):
    cadena_hotelera = get_object_or_404(CadenaHotelera, pk=pk)
    if request.method == 'POST':
        cadena_hotelera.delete()
        return redirect('listar_cadenas_hoteleras')
    return render(request, 'backoffice/cadena_hotelera/eliminar_cadena_hotelera.html', {'cadena_hotelera': cadena_hotelera})


# ---------------------------------------- HABITACIONES ---------------------------------------- #
@manager_required
@login_required
def listar_habitaciones(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = Habitacion.objects.filter(hotel=hotel)

    context = {
        'hotel': hotel,
        'habitaciones': habitaciones
    }

    return render(request, 'backoffice/listar_habitaciones.html', context)

@manager_required
@login_required
def crear_habitacion(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    context = {
        'hotel': hotel,
    }
    return render(request, 'backoffice/hotel_rooms.html', context)

@manager_required
@login_required
def eliminar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    hotel_id = habitacion.hotel.id

    if request.method == 'POST':
        habitacion.delete()
        # Redirige usando el namespace si corresponde
        return redirect(reverse('backoffice:editar_hotel', args=[hotel_id]))

    context = {
        'habitacion': habitacion,
        'hotel_id': hotel_id
    }

    return render(request, 'backoffice/eliminar_habitacion.html', context)

# ---------------------------------------- HABITACIONES OFERTAS ---------------------------------------- #
@manager_required
@login_required
def hotel_offers(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = hotel.habitaciones.all()  # Usar el related_name definido en el modelo Habitacion
    ofertas = Oferta.objects.filter(hotel=hotel)

    context = {
        'hotel': hotel,
        'habitaciones': habitaciones,
        'ofertas': ofertas,
    }
    return render(request, 'backoffice/hotel_offers.html', context)

@manager_required
@login_required
def hotel_crear_offers(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = hotel.habitaciones.all()  # Usar el related_name definido en el modelo Habitacion
    context = {
        'hotel': hotel,
        'habitaciones': habitaciones,
    }
    return render(request, 'backoffice/hotel_crear_offers.html', context)

@manager_required
@login_required
def guardar_oferta(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    if request.method == 'POST':
        disponible = request.POST.get('disponible') == 'on'
        codigo = request.POST.get('codigo_oferta')
        tipo_habitacion = request.POST.get('tipoHabitacion_oferta')
        temporada = request.POST.get('temporada')
        booking_window = request.POST.get('booking_window')
        sencilla = request.POST.get('sencilla_oferta')
        doble = request.POST.get('doble_oferta')
        triple = request.POST.get('triple_oferta')
        primer_nino = request.POST.get('primerNino_oferta')
        segundo_nino = request.POST.get('segundoNino_oferta')
        un_adulto_con_ninos = request.POST.get('un_adulto_con_ninos')
        primer_nino_con_un_adulto = request.POST.get('primer_nino_con_un_adulto')
        segundo_nino_con_un_adulto = request.POST.get('segundo_nino_con_un_adulto')
        edad_nino = request.POST.get('edad_nino')
        edad_infante = request.POST.get('edad_infante')
        noches_minimas = request.POST.get('noches_minimas')

        oferta = Oferta(
            hotel=hotel,
            disponible=disponible,
            codigo=codigo,
            tipo_habitacion=tipo_habitacion,
            temporada=temporada,
            booking_window=booking_window,
            sencilla=sencilla,
            doble=doble,
            triple=triple,
            primer_nino=primer_nino,
            segundo_nino=segundo_nino,
            un_adulto_con_ninos=un_adulto_con_ninos,
            primer_nino_con_un_adulto=primer_nino_con_un_adulto,
            segundo_nino_con_un_adulto=segundo_nino_con_un_adulto,
            edad_nino=edad_nino,
            edad_infante=edad_infante,
            noches_minimas=noches_minimas,
        )
        oferta.save()

        return redirect('backoffice:hotel_offers', hotel_id=hotel_id)

    context = {
        'hotel': hotel,
    }
    return render(request, 'backoffice/hotel_crear_offers.html', context)

@manager_required
@login_required
def eliminar_oferta(request, oferta_id):
    oferta = get_object_or_404(Oferta, id=oferta_id)
    hotel_id = oferta.hotel.id
    oferta.delete()
    return redirect('backoffice:hotel_offers', hotel_id=hotel_id)

@manager_required
@login_required
def cargar_datos_hoteles(request, hotel_id):
    ruta_archivo = os.path.join('backoffice/static/backoffice/plantilla_hoteles.xlsx')
    datos_hoteles = leer_datos_hoteles(ruta_archivo)
    
    # Obtener el nombre del hotel de los parámetros de la solicitud
    hotel = get_object_or_404(Hotel, id=hotel_id)
    print(f"Hotel: ID: {hotel.id}, Nombre: {hotel.hotel_nombre}")
    
    hotel_nombre = hotel.hotel_nombre
    hotel_data = next((hotel for hotel in datos_hoteles if hotel['nombre_hotel'] == hotel_nombre), None)
    print(f"Hotel data: {hotel_data}")
    habitaciones = hotel_data['habitaciones'] if hotel_data else []

    return JsonResponse({'ofertas': habitaciones})

@manager_required
@login_required
def eliminar_oferta(request, hotel_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            oferta_id = data.get('id')
            oferta = Oferta.objects.get(id=oferta_id)
            oferta.delete()
            return JsonResponse({'status': 'success'}, status=200)
        except Oferta.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Oferta no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@manager_required
@login_required
def guardar_todas_ofertas(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        ofertas_data = json.loads(request.body).get('ofertas', [])

        for oferta_data in ofertas_data:
            temporada = oferta_data['temporada']
            booking_window = oferta_data['booking_window']
            tipo_habitacion = oferta_data['tipo_habitacion']
            cantidad_habitaciones = oferta_data.get('cantidad_habitaciones', 1)

            # Verificar que no existan dos ofertas con la misma temporada exacta
            if Oferta.objects.filter(hotel=hotel, tipo_habitacion=tipo_habitacion, temporada=temporada, booking_window=booking_window).exists():
                continue

            oferta = Oferta(
                hotel=hotel,
                disponible=oferta_data['disponible'],
                codigo=oferta_data['codigo'],
                tipo_habitacion=tipo_habitacion,
                temporada=temporada,
                booking_window=booking_window,
                sencilla=oferta_data['sencilla'],
                doble=oferta_data['doble'],
                triple=oferta_data['triple'],
                primer_nino=oferta_data['primer_nino'],
                segundo_nino=oferta_data['segundo_nino'],
                un_adulto_con_ninos=oferta_data['un_adulto_con_ninos'],
                primer_nino_con_un_adulto=oferta_data['primer_nino_con_un_adulto'],
                segundo_nino_con_un_adulto=oferta_data['segundo_nino_con_un_adulto'],
                edad_nino=oferta_data['edad_nino'],
                edad_infante=oferta_data['edad_infante'],
                noches_minimas=oferta_data['noches_minimas'],
                cantidad_habitaciones=cantidad_habitaciones,
                tipo_fee=oferta_data.get('tipo_fee'),                  # Nuevo campo
                fee_doble=oferta_data.get('fee_doble'),                # Nuevo campo
                fee_triple=oferta_data.get('fee_triple'),              # Nuevo campo
                fee_sencilla=oferta_data.get('fee_sencilla'),          # Nuevo campo
                fee_primer_nino=oferta_data.get('fee_primer_nino'),    # Nuevo campo
                fee_segundo_nino=oferta_data.get('fee_segundo_nino')   # Nuevo campo
            )
            oferta.save()

        return JsonResponse({'message': 'Ofertas guardadas exitosamente'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@manager_required
@login_required
def guardar_instalaciones_hotel(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        data = request.POST
        
        facility, created = HotelFacility.objects.update_or_create(
            hotel=hotel,  # Usa el campo de relación correctamente
            defaults={
                'articulos_aseo': data.get('articulos_aseo') == 'true',
                'inodoro': data.get('inodoro') == 'true',
                'toallas': data.get('toallas') == 'true',
                'bano_privado': data.get('bano_privado') == 'true',
                'banera_ducha': data.get('banera_ducha') == 'true',
                'secador_pelo': data.get('secador_pelo') == 'true',
                'extintores': data.get('extintores') == 'true',
                'detectores_humo': data.get('detectores_humo') == 'true',
                'cctv': data.get('cctv') == 'true',
                'ropa_cama': data.get('ropa_cama') == 'true',
                'armario_ropero': data.get('armario_ropero') == 'true',
                'bar': data.get('bar') == 'true',
                'restaurante': data.get('restaurante') == 'true',
                'menu_ninos': data.get('menu_ninos') == 'true',
                'menu_dietetico': data.get('menu_dietetico') == 'true',
                'desayuno': data.get('desayuno') == 'true',
                'tetera_cafetera': data.get('tetera_cafetera') == 'true',
                'ascensor': data.get('ascensor') == 'true',
                'discapacitados': data.get('discapacitados') == 'true',
                'hipoalergenico': data.get('hipoalergenico') == 'true',
                'habitaciones_familiares': data.get('habitaciones_familiares') == 'true',
                'prohibido_fumar': data.get('prohibido_fumar') == 'true',
                'calefaccion': data.get('calefaccion') == 'true',
                'alfombrado': data.get('alfombrado') == 'true',
                'instalaciones_planchar': data.get('instalaciones_planchar') == 'true',
                'plancha': data.get('plancha') == 'true',
                'guardaequipaje': data.get('guardaequipaje') == 'true',
                'factura_proporcionada': data.get('factura_proporcionada') == 'true',
                'recepcion_24h': data.get('recepcion_24h') == 'true',
                'checkin_checkout_privado': data.get('checkin_checkout_privado') == 'true',
                'tv_pantalla_plana': data.get('tv_pantalla_plana') == 'true',
                'radio': data.get('radio') == 'true',
                'canales_via_satellite': data.get('canales_via_satellite') == 'true',
                'tv': data.get('tv') == 'true',
                'telefono': data.get('telefono') == 'true',
                'lavanderia': data.get('lavanderia') == 'true',
                'tintoreria': data.get('tintoreria') == 'true',
                'limpieza_diaria': data.get('limpieza_diaria') == 'true'
            }
        )
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'fail'}, status=400)

@manager_required
@login_required
def guardar_configuracion_hotel(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        data = request.POST
        
        setting, created = HotelSetting.objects.update_or_create(
            hotel=hotel,
            defaults={
                'edad_limite_primer_nino': int(data.get('edadLimite_primerNino', 0)),
                'edad_limite_infante': int(data.get('edadLimite_infante', 0)),
                'cantidad_noches': int(data.get('cantidad_noches', 0)),
            }
        )
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'fail'}, status=400)


# ---------------------------------------- RESERVAS ---------------------------------------- #
@manager_required
@login_required
def listar_reservas(request, estado=None):
    reservas = Reserva.objects.all().order_by('fecha_reserva')
    
    # Filtrar por estado
    if estado:
        if estado == 'por_cobrar':
            reservas = reservas.filter(cobrada=False)
        elif estado == 'pagada':
            reservas = reservas.filter(pagada=True)
        else:
            reservas = reservas.filter(estatus=estado)

    # Filtrar por query de búsqueda
    query = request.GET.get('q', '')
    if query:
        reservas = reservas.filter(
            Q(hotel__hotel_nombre__icontains=query) |
            Q(nombre_usuario__icontains=query) |
            Q(email_empleado__icontains=query)
        )

    # Filtrar por ID de Reserva
    id_reserva = request.GET.get('id_reserva', '')
    if id_reserva:
        reservas = reservas.filter(id=id_reserva)

    # Filtrar por Nombre del Pasajero
    nombre_pasajero = request.GET.get('nombre_pasajero', '')
    if nombre_pasajero:
        reservas = reservas.filter(habitaciones_reserva__pasajeros__nombre__icontains=nombre_pasajero)

    # Filtrar por Rango de Fechas
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    if fecha_inicio:
        reservas = reservas.filter(fecha_reserva__gte=fecha_inicio)
    if fecha_fin:
        reservas = reservas.filter(fecha_reserva__lte=fecha_fin)

    # Paginación de las reservas
    paginator = Paginator(reservas, 10)  # 10 reservas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reservas': page_obj,
        'query': query,
        'estado': estado,
        'id_reserva': id_reserva,
        'nombre_pasajero': nombre_pasajero,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'backoffice/reservas/listar_reservas.html', context)

@manager_required
@login_required
def detalles_reserva(request, reserva_id):
    
    try:
        # Intenta obtener la reserva por su ID
        reserva = Reserva.objects.get(pk=reserva_id)
        
        # Obtener datos del hotel y verificaciones
        hotel_nombre = getattr(reserva.hotel, 'hotel_nombre', 'Hotel no disponible')
        
        direccion = getattr(reserva.hotel, 'direccion', 'Dirección no disponible')
        
        # Verificar fechas de check-in y check-out
        checkin = reserva.fecha_reserva.strftime('%Y-%m-%d %H:%M')
        checkout = (reserva.fecha_reserva + timedelta(days=10)).strftime('%Y-%m-%d %H:%M')  # Ajustar según tu lógica
        
        # Construcción de la lista de habitaciones
        habitaciones = []
        for habitacion in reserva.habitaciones_reserva.all():
            
            adultos = ', '.join([p.nombre for p in habitacion.pasajeros.filter(tipo='adulto')])
            ninos = ', '.join([p.nombre for p in habitacion.pasajeros.filter(tipo='nino')])
            
            habitaciones.append({
                'nombre': habitacion.habitacion_nombre,
                'adultos': adultos,
                'ninos': ninos
            })

        # Construye la respuesta JSON con los detalles de la reserva
        data = {
            'hotel': hotel_nombre,
            'direccion': direccion,
            'checkin': checkin,
            'checkout': checkout,
            'habitaciones': habitaciones
        }
       
        return JsonResponse(data)

    except Reserva.DoesNotExist:
        print("Reserva no encontrada con ID:", reserva_id)
        return JsonResponse({'error': 'Reserva no encontrada.'}, status=404)

    except Exception as e:
        # Captura otros errores y los muestra en la consola del servidor
        print(f"Error al obtener los detalles de la reserva: {e}")
        return JsonResponse({'error': 'Error al cargar los detalles de la reserva.'}, status=500)

@manager_required
@login_required
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('backoffice:listar_reservas')  # Usa el namespace aquí
    else:
        form = ReservaForm()
    return render(request, 'backoffice/reservas/editar_reserva.html', {'form': form})

@manager_required
@login_required
def eliminar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        reserva.delete()
        return redirect('backoffice:listar_reservas')  # Usa el namespace aquí
    return render(request, 'backoffice/reservas/eliminar_reserva.html', {'reserva': reserva})

# -------------------------------------------------------------------------------- #

@manager_required
@login_required
def edit_reserva_load(request, reserva_id):
    # ------------------------------------------------------
    # Función para cargar los datos de una reserva existente.
    # Obtiene la reserva, sus habitaciones, y los pasajeros asociados.
    # Renderiza la página de edición de la reserva con la información cargada.
    # ------------------------------------------------------
    # Cargar la reserva existente
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    
    # Cargar las habitaciones asociadas, junto con los pasajeros
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva).prefetch_related('pasajeros')
    
    tipos_habitacion = Habitacion.objects.filter(hotel=reserva.hotel)
    
    # Pasar la reserva y habitaciones a la plantilla
    return render(request, 'backoffice/reservas/edit_reserva.html', {
        'reserva': reserva,
        'habitaciones': habitaciones,
        'tipos_habitacion': tipos_habitacion,
    })

@manager_required
@login_required

def edit_reserva_save(request, reserva_id):
    """
    Vista para guardar cambios en una reserva.
    Según el tipo de reserva (hoteles o traslados), se actualizan los campos generales y los detalles específicos.
    """
    if request.method == 'POST':
        reserva = get_object_or_404(Reserva, pk=reserva_id)
        
        # Actualizar los campos generales de la reserva
        actualizar_reserva_principal(request, reserva)
        
        if reserva.tipo == 'hoteles':
            # Para reservas de hoteles se actualizan habitaciones y pasajeros
            actualizar_habitaciones_y_pasajeros(request, reserva)
            agregar_nuevas_habitaciones(request, reserva)
            nuevo_precio_total = recalcular_precio_y_costo(reserva)
            reserva.precio_total = nuevo_precio_total
        elif reserva.tipo == 'traslados':
            # Para reservas de traslados se actualizan los datos del traslado y sus pasajeros
            actualizar_traslado_y_pasajeros(request, reserva)
            # Aquí podrías recalcular el precio para traslados si la lógica es diferente
            # reserva.precio_total = nuevo_precio_traslado (si aplica)
        
        reserva.save()
        
        # Si la reserva está confirmada, se envía el correo de confirmación (con voucher/factura si corresponde)
        if reserva.estatus == 'confirmada':
            correo_confirmada(reserva)
        
        return redirect('backoffice:listar_reservas')
    
    return redirect('backoffice:edit_reserva_load', reserva_id=reserva_id)


def actualizar_reserva_principal(request, reserva):
    """
    Actualiza los campos generales de la reserva (independientemente del tipo).
    """
    reserva.nombre_usuario = request.POST.get('nombre_usuario', reserva.nombre_usuario)
    reserva.email_empleado = request.POST.get('email_empleado', reserva.email_empleado)
    reserva.costo_total = request.POST.get('costo_total', reserva.costo_total)
    reserva.precio_total = request.POST.get('precio_total', reserva.precio_total)
    reserva.tipo = request.POST.get('tipo', reserva.tipo)
    reserva.estatus = request.POST.get('estatus', reserva.estatus)
    reserva.numero_confirmacion = request.POST.get('numero_confirmacion', reserva.numero_confirmacion)
    reserva.notas = request.POST.get('notas', reserva.notas)
    
    # Campos booleanos
    reserva.cobrada = True if request.POST.get('cobrada') == 'on' else False
    reserva.pagada = True if request.POST.get('pagada') == 'on' else False

    try:
        reserva.save()
        print(f'Reserva {reserva.id} actualizada exitosamente.')
    except Exception as e:
        print(f'Error al guardar la reserva {reserva.id}: {e}')


def actualizar_traslado_y_pasajeros(request, reserva):
    """
    Actualiza los detalles específicos de un traslado y sus pasajeros.
    Se espera que la reserva tenga un objeto 'traslado' asociado.
    """
    # Importar modelos necesarios (si no están importados globalmente)
    from backoffice.models import Transportista, Ubicacion, Vehiculo

    traslado = reserva.traslado

    # Actualizar campos del traslado
    transportista_name = request.POST.get('transportista')
    origen_name = request.POST.get('origen')
    destino_name = request.POST.get('destino')
    vehiculo_tipo = request.POST.get('vehiculo')
    costo_traslado = request.POST.get('costo_traslado')

    try:
        costo_traslado = float(costo_traslado)
    except (TypeError, ValueError):
        costo_traslado = traslado.costo  # O dejar el costo anterior si hay error

    try:
        traslado.transportista = Transportista.objects.get(nombre=transportista_name)
    except Transportista.DoesNotExist:
        print(f"No se encontró el transportista '{transportista_name}'.")
    try:
        traslado.origen = Ubicacion.objects.get(nombre=origen_name)
    except Ubicacion.DoesNotExist:
        print(f"No se encontró el origen '{origen_name}'.")
    try:
        traslado.destino = Ubicacion.objects.get(nombre=destino_name)
    except Ubicacion.DoesNotExist:
        print(f"No se encontró el destino '{destino_name}'.")
    try:
        traslado.vehiculo = Vehiculo.objects.get(tipo=vehiculo_tipo)
    except Vehiculo.DoesNotExist:
        print(f"No se encontró el vehículo '{vehiculo_tipo}'.")
    
    traslado.costo = costo_traslado
    traslado.save()

    # Actualizar pasajeros existentes asociados al traslado
    for pasajero in traslado.pasajeros.all():
        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
        
        if fecha_nacimiento:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                fecha_nacimiento = pasajero.fecha_nacimiento
        if caducidad_pasaporte:
            try:
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                caducidad_pasaporte = pasajero.caducidad_pasaporte

        pasajero.nombre = nombre
        pasajero.fecha_nacimiento = fecha_nacimiento
        pasajero.pasaporte = pasaporte
        pasajero.caducidad_pasaporte = caducidad_pasaporte
        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
        pasajero.tipo = tipo
        pasajero.save()

    # Agregar nuevos pasajeros para el traslado
    for key in request.POST:
        if key.startswith('traslado_pasajero_nombre_'):
            new_id = key.split('_')[-1]
            nombre = request.POST.get(f'traslado_pasajero_nombre_{new_id}')
            fecha_nacimiento = request.POST.get(f'traslado_pasajero_fecha_nacimiento_{new_id}')
            pasaporte = request.POST.get(f'traslado_pasajero_pasaporte_{new_id}')
            caducidad_pasaporte = request.POST.get(f'traslado_pasajero_caducidad_pasaporte_{new_id}')
            pais_emision_pasaporte = request.POST.get(f'traslado_pasajero_pais_emision_pasaporte_{new_id}')
            tipo = request.POST.get(f'traslado_pasajero_tipo_{new_id}')
            
            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
                print(f"Datos incompletos para pasajero nuevo en traslado: {nombre}")
                continue
            
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                print(f"Error al convertir fechas para pasajero nuevo: {nombre}")
                continue
            
            Pasajero.objects.create(
                traslado=traslado,
                nombre=nombre,
                fecha_nacimiento=fecha_nacimiento,
                pasaporte=pasaporte,
                caducidad_pasaporte=caducidad_pasaporte,
                pais_emision_pasaporte=pais_emision_pasaporte,
                tipo=tipo
            )


def actualizar_habitaciones_y_pasajeros(request, reserva):
    """
    Actualiza las habitaciones y pasajeros para reservas de hoteles.
    """
    habitaciones = HabitacionReserva.objects.filter(reserva_id=reserva.id)
    
    for habitacion in habitaciones:
        actualizar_habitacion(request, habitacion)
        actualizar_pasajeros_existentes(request, habitacion)
        agregar_nuevos_pasajeros(request, habitacion)
    
    recalcular_precio_y_costo(reserva)


def actualizar_habitacion(request, habitacion):
    habitacion_nombre = request.POST.get(f'habitacion_nombre_{habitacion.id}')
    adultos = request.POST.get(f'adultos_{habitacion.id}')
    ninos = request.POST.get(f'ninos_{habitacion.id}')
    fechas_viaje = request.POST.get(f'fechas_viaje_{habitacion.id}')
    
    if fechas_viaje and fechas_viaje != 'Invalid date':
        try:
            fechas_viaje = datetime.strptime(fechas_viaje, '%Y/%m/%d').strftime('%Y-%m-%d')
        except ValueError:
            fechas_viaje = habitacion.fechas_viaje
    habitacion.habitacion_nombre = habitacion_nombre
    habitacion.adultos = adultos
    habitacion.ninos = ninos
    habitacion.fechas_viaje = fechas_viaje
    habitacion.save()


def actualizar_pasajeros_existentes(request, habitacion):
    for pasajero in habitacion.pasajeros.all():
        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
        
        if fecha_nacimiento and fecha_nacimiento != 'Invalid date':
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                fecha_nacimiento = pasajero.fecha_nacimiento
        if caducidad_pasaporte and caducidad_pasaporte != 'Invalid date':
            try:
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                caducidad_pasaporte = pasajero.caducidad_pasaporte
        
        pasajero.nombre = nombre
        pasajero.fecha_nacimiento = fecha_nacimiento
        pasajero.pasaporte = pasaporte
        pasajero.caducidad_pasaporte = caducidad_pasaporte
        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
        pasajero.tipo = tipo
        pasajero.save()


def agregar_nuevos_pasajeros(request, habitacion):
    total_adultos = int(habitacion.adultos) if habitacion.adultos else 0
    total_ninos = int(habitacion.ninos) if habitacion.ninos else 0

    for key in request.POST:
        if key.startswith(f'habitacion_{habitacion.id}_pasajero_nombre_'):
            new_passenger_id = key.split('_')[-1]
            nombre = request.POST.get(f'habitacion_{habitacion.id}_pasajero_nombre_{new_passenger_id}')
            fecha_nacimiento = request.POST.get(f'habitacion_{habitacion.id}_pasajero_fecha_nacimiento_{new_passenger_id}')
            pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pasaporte_{new_passenger_id}')
            caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_caducidad_pasaporte_{new_passenger_id}')
            pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pais_emision_pasaporte_{new_passenger_id}')
            tipo = request.POST.get(f'habitacion_{habitacion.id}_pasajero_tipo_{new_passenger_id}')

            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
                print(f"Error: Faltan datos obligatorios para el pasajero {nombre}. No se guardará.")
                continue

            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                print(f"Error al convertir fechas para el pasajero {nombre}.")
                continue

            if not Pasajero.objects.filter(habitacion=habitacion, nombre=nombre, pasaporte=pasaporte).exists():
                nuevo_pasajero = Pasajero.objects.create(
                    habitacion=habitacion,
                    nombre=nombre,
                    fecha_nacimiento=fecha_nacimiento,
                    pasaporte=pasaporte,
                    caducidad_pasaporte=caducidad_pasaporte,
                    pais_emision_pasaporte=pais_emision_pasaporte,
                    tipo=tipo
                )
                if tipo == 'adulto':
                    total_adultos += 1
                else:
                    total_ninos += 1

    habitacion.adultos = total_adultos
    habitacion.ninos = total_ninos
    habitacion.save()


def agregar_nuevas_habitaciones(request, reserva):
    habitacion_counter = reserva.habitaciones_reserva.count() + 1
    while True:
        habitacion_nombre = request.POST.get(f'nueva_habitacion_nombre_{habitacion_counter}')
        if not habitacion_nombre:
            break
        adultos = int(request.POST.get(f'nueva_adultos_{habitacion_counter}', 0))
        ninos = int(request.POST.get(f'nueva_ninos_{habitacion_counter}', 0))
        fechas_viaje_antes = request.POST.get(f'nueva_fechas_viaje_{habitacion_counter}')
        fechas_viaje = fechas_viaje_antes.replace('/', '-') if fechas_viaje_antes else '2024-01-01'
        if fechas_viaje and fechas_viaje != 'Invalid date':
            try:
                fechas_viaje = fechas_viaje.strip()
            except ValueError:
                fechas_viaje = '2024-01-01'
        else:
            fechas_viaje = '2024-01-01'
        precio = 100.00  # Ajusta según la lógica de tu negocio
        oferta_codigo = "OFERTA2024"  # Ajusta según corresponda
        nueva_habitacion = HabitacionReserva.objects.create(
            reserva=reserva,
            habitacion_nombre=habitacion_nombre,
            adultos=adultos,
            ninos=ninos,
            fechas_viaje=fechas_viaje,
            precio=precio,
            oferta_codigo=oferta_codigo
        )
        agregar_nuevos_pasajeros_a_habitacion_nueva(request, nueva_habitacion, habitacion_counter)
        habitacion_counter += 1


def agregar_nuevos_pasajeros_a_habitacion_nueva(request, habitacion, habitacion_counter):
    pasajero_counter = 1
    while True:
        nombre = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_nombre')
        if not nombre:
            break
        fecha_nacimiento = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_fecha_nacimiento')
        pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pasaporte')
        caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_caducidad_pasaporte')
        pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pais_emision_pasaporte')
        tipo = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_tipo')

        if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
            break

        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
        except ValueError:
            break

        Pasajero.objects.create(
            habitacion=habitacion,
            nombre=nombre,
            fecha_nacimiento=fecha_nacimiento,
            pasaporte=pasaporte,
            caducidad_pasaporte=caducidad_pasaporte,
            pais_emision_pasaporte=pais_emision_pasaporte,
            tipo=tipo
        )
        pasajero_counter += 1


def correo_confirmada(reserva):
    """
    Envía el correo de confirmación (para reservas de hoteles, por ahora).
    """
    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
    encabezado = "{% trans 'Muchas gracias por reservar con RUTA MULTISERVICE, su solicitud ha sido confirmada:' %}"
    enviar_correo(reserva, pasajeros, habitaciones, reserva.email_empleado, encabezado)


def recalcular_precio_y_costo(reserva):
    habitaciones_reserva = HabitacionReserva.objects.filter(reserva=reserva)
    precio_total = 0
    for habitacion_reserva in habitaciones_reserva:
        cant_adultos = habitacion_reserva.adultos
        habitacion_nombre = habitacion_reserva.habitacion_nombre
        fecha_viaje = habitacion_reserva.fechas_viaje
        nombre_hotel = reserva.hotel.hotel_nombre
        habitacion = obtener_habitacion(nombre_hotel, habitacion_nombre)
        ofertas = obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre)
        if habitacion_reserva.ninos == 1:
            nino1 = 1; nino2 = 0
        elif habitacion_reserva.ninos == 2:
            nino1 = 1; nino2 = 1
        else:
            nino1 = 0; nino2 = 0
        if habitacion and ofertas:
            dias_oferta = calcular_dias_por_oferta(ofertas, fecha_viaje)
            for result in dias_oferta:
                precio_total += calcula_precio(cant_adultos, nino1, nino2, result["oferta"], habitacion, result["dias_en_oferta"])
    return precio_total


def actualizar_habitacion(request, habitacion):
    habitacion_nombre = request.POST.get(f'habitacion_nombre_{habitacion.id}')
    adultos = request.POST.get(f'adultos_{habitacion.id}')
    ninos = request.POST.get(f'ninos_{habitacion.id}')
    fechas_viaje = request.POST.get(f'fechas_viaje_{habitacion.id}')
    if fechas_viaje and fechas_viaje != 'Invalid date':
        try:
            fechas_viaje = datetime.strptime(fechas_viaje, '%Y/%m/%d').strftime('%Y-%m-%d')
        except ValueError:
            fechas_viaje = habitacion.fechas_viaje
    habitacion.habitacion_nombre = habitacion_nombre
    habitacion.adultos = adultos
    habitacion.ninos = ninos
    habitacion.fechas_viaje = fechas_viaje
    habitacion.save()


def actualizar_pasajeros_existentes(request, habitacion):
    for pasajero in habitacion.pasajeros.all():
        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
        if fecha_nacimiento and fecha_nacimiento != 'Invalid date':
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                fecha_nacimiento = pasajero.fecha_nacimiento
        if caducidad_pasaporte and caducidad_pasaporte != 'Invalid date':
            try:
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                caducidad_pasaporte = pasajero.caducidad_pasaporte
        pasajero.nombre = nombre
        pasajero.fecha_nacimiento = fecha_nacimiento
        pasajero.pasaporte = pasaporte
        pasajero.caducidad_pasaporte = caducidad_pasaporte
        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
        pasajero.tipo = tipo
        pasajero.save()


def agregar_nuevos_pasajeros(request, habitacion):
    total_adultos = int(habitacion.adultos) if habitacion.adultos else 0
    total_ninos = int(habitacion.ninos) if habitacion.ninos else 0
    for key in request.POST:
        if key.startswith(f'habitacion_{habitacion.id}_pasajero_nombre_'):
            new_passenger_id = key.split('_')[-1]
            nombre = request.POST.get(f'habitacion_{habitacion.id}_pasajero_nombre_{new_passenger_id}')
            fecha_nacimiento = request.POST.get(f'habitacion_{habitacion.id}_pasajero_fecha_nacimiento_{new_passenger_id}')
            pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pasaporte_{new_passenger_id}')
            caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_caducidad_pasaporte_{new_passenger_id}')
            pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pais_emision_pasaporte_{new_passenger_id}')
            tipo = request.POST.get(f'habitacion_{habitacion.id}_pasajero_tipo_{new_passenger_id}')
            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
                print(f"Error: Faltan datos obligatorios para el pasajero {nombre}. No se guardará.")
                continue
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                print(f"Error al convertir las fechas para el pasajero {nombre}.")
                continue
            if not Pasajero.objects.filter(habitacion=habitacion, nombre=nombre, pasaporte=pasaporte).exists():
                Pasajero.objects.create(
                    habitacion=habitacion,
                    nombre=nombre,
                    fecha_nacimiento=fecha_nacimiento,
                    pasaporte=pasaporte,
                    caducidad_pasaporte=caducidad_pasaporte,
                    pais_emision_pasaporte=pais_emision_pasaporte,
                    tipo=tipo
                )
                if tipo == 'adulto':
                    total_adultos += 1
                else:
                    total_ninos += 1
    habitacion.adultos = total_adultos
    habitacion.ninos = total_ninos
    habitacion.save()


def agregar_nuevos_pasajeros_a_habitacion_nueva(request, habitacion, habitacion_counter):
    pasajero_counter = 1
    while True:
        nombre = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_nombre')
        if not nombre:
            break
        fecha_nacimiento = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_fecha_nacimiento')
        pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pasaporte')
        caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_caducidad_pasaporte')
        pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pais_emision_pasaporte')
        tipo = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_tipo')
        if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
            break
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
        except ValueError:
            break
        Pasajero.objects.create(
            habitacion=habitacion,
            nombre=nombre,
            fecha_nacimiento=fecha_nacimiento,
            pasaporte=pasaporte,
            caducidad_pasaporte=caducidad_pasaporte,
            pais_emision_pasaporte=pais_emision_pasaporte,
            tipo=tipo
        )
        pasajero_counter += 1


def correo_confirmada(reserva):
    """
    Envía el correo de confirmación (para reservas de hoteles, por ahora).
    """
    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
    encabezado = "{% trans 'Muchas gracias por reservar con RUTA MULTISERVICE, su solicitud ha sido confirmada:' %}"
    enviar_correo(reserva, pasajeros, habitaciones, reserva.email_empleado, encabezado)


def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, cant_dias):
    # ... (Lógica de cálculo de precio para hoteles)
    # Esta función se mantiene sin cambios.
    pass  # Usa tu implementación actual aquí


def calcular_dias_por_oferta(ofertas, fecha_viaje):
    try:
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
    except ValueError as e:
        print(f"Error al parsear fechas de viaje: {e}")
        raise
    resultado = []
    for oferta in ofertas:
        try:
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
        except ValueError as e:
            print(f"Error al parsear fechas de la oferta {oferta}: {e}")
            continue
        inicio_solapamiento = max(fecha_inicio_viaje, fecha_inicio_oferta)
        fin_solapamiento = min(fecha_fin_viaje, fecha_fin_oferta)
        if inicio_solapamiento <= fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days + 1
            resultado.append({
                "oferta": oferta,
                "dias_en_oferta": dias_en_oferta
            })
    return resultado


def obtener_habitacion(nombre_hotel, nombre_habitacion):
    try:
        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
        habitacion = Habitacion.objects.get(hotel=hotel, tipo=nombre_habitacion)
        return habitacion
    except ObjectDoesNotExist:
        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{nombre_habitacion}'.")
        return None


def obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre):
    try:
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
        ofertas = Oferta.objects.filter(
            hotel=hotel,
            tipo_habitacion=habitacion_nombre,
            disponible=True
        )
        ofertas_validas = []
        for oferta in ofertas:
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
            if fecha_inicio_viaje <= fecha_fin_oferta and fecha_fin_viaje >= fecha_inicio_oferta:
                ofertas_validas.append(oferta)
        return ofertas_validas
    except ObjectDoesNotExist:
        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{habitacion_nombre}'.")
        return []
    except ValueError as e:
        print(f"Error al parsear las fechas: {e}")
        return []


def recalcular_precio_y_costo(reserva):
    habitaciones_reserva = HabitacionReserva.objects.filter(reserva=reserva)
    precio_total = 0
    for habitacion_reserva in habitaciones_reserva:
        cant_adultos = habitacion_reserva.adultos
        habitacion_nombre = habitacion_reserva.habitacion_nombre
        fecha_viaje = habitacion_reserva.fechas_viaje
        nombre_hotel = reserva.hotel.hotel_nombre
        habitacion = obtener_habitacion(nombre_hotel, habitacion_nombre)
        ofertas = obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre)
        if habitacion_reserva.ninos == 1:
            nino1 = 1; nino2 = 0
        elif habitacion_reserva.ninos == 2:
            nino1 = 1; nino2 = 1
        else:
            nino1 = 0; nino2 = 0
        if habitacion and ofertas:
            dias_oferta = calcular_dias_por_oferta(ofertas, fecha_viaje)
            for result in dias_oferta:
                precio_total += calcula_precio(cant_adultos, nino1, nino2, result["oferta"], habitacion, result["dias_en_oferta"])
    return precio_total


def actualizar_traslado_y_pasajeros(request, reserva):
    """
    Actualiza los campos específicos de un traslado y sus pasajeros.
    Se asume que la reserva tiene un objeto 'traslado' asociado.
    """
    from backoffice.models import Transportista, Ubicacion, Vehiculo  # Asegúrate de tenerlos importados
    traslado = reserva.traslado

    transportista_name = request.POST.get('transportista')
    origen_name = request.POST.get('origen')
    destino_name = request.POST.get('destino')
    vehiculo_tipo = request.POST.get('vehiculo')
    costo_traslado = request.POST.get('costo_traslado')
    try:
        costo_traslado = float(costo_traslado)
    except (TypeError, ValueError):
        costo_traslado = traslado.costo

    try:
        traslado.transportista = Transportista.objects.get(nombre=transportista_name)
    except Transportista.DoesNotExist:
        print(f"No se encontró el transportista '{transportista_name}'.")
    try:
        traslado.origen = Ubicacion.objects.get(nombre=origen_name)
    except Ubicacion.DoesNotExist:
        print(f"No se encontró el origen '{origen_name}'.")
    try:
        traslado.destino = Ubicacion.objects.get(nombre=destino_name)
    except Ubicacion.DoesNotExist:
        print(f"No se encontró el destino '{destino_name}'.")
    try:
        traslado.vehiculo = Vehiculo.objects.get(tipo=vehiculo_tipo)
    except Vehiculo.DoesNotExist:
        print(f"No se encontró el vehículo '{vehiculo_tipo}'.")
    
    traslado.costo = costo_traslado
    traslado.save()

    # Actualizar pasajeros existentes en el traslado
    for pasajero in traslado.pasajeros.all():
        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
        if fecha_nacimiento:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                fecha_nacimiento = pasajero.fecha_nacimiento
        if caducidad_pasaporte:
            try:
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                caducidad_pasaporte = pasajero.caducidad_pasaporte
        pasajero.nombre = nombre
        pasajero.fecha_nacimiento = fecha_nacimiento
        pasajero.pasaporte = pasaporte
        pasajero.caducidad_pasaporte = caducidad_pasaporte
        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
        pasajero.tipo = tipo
        pasajero.save()

    # Agregar nuevos pasajeros para el traslado
    for key in request.POST:
        if key.startswith('traslado_pasajero_nombre_'):
            new_id = key.split('_')[-1]
            nombre = request.POST.get(f'traslado_pasajero_nombre_{new_id}')
            fecha_nacimiento = request.POST.get(f'traslado_pasajero_fecha_nacimiento_{new_id}')
            pasaporte = request.POST.get(f'traslado_pasajero_pasaporte_{new_id}')
            caducidad_pasaporte = request.POST.get(f'traslado_pasajero_caducidad_pasaporte_{new_id}')
            pais_emision_pasaporte = request.POST.get(f'traslado_pasajero_pais_emision_pasaporte_{new_id}')
            tipo = request.POST.get(f'traslado_pasajero_tipo_{new_id}')
            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
                continue
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                continue
            Pasajero.objects.create(
                traslado=traslado,
                nombre=nombre,
                fecha_nacimiento=fecha_nacimiento,
                pasaporte=pasaporte,
                caducidad_pasaporte=caducidad_pasaporte,
                pais_emision_pasaporte=pais_emision_pasaporte,
                tipo=tipo
            )


# Las siguientes funciones se mantienen o se implementan según tu lógica actual:
def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, cant_dias):
    # Lógica actual para calcular el precio en reservas de hoteles
    pass


def calcular_dias_por_oferta(ofertas, fecha_viaje):
    try:
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
    except ValueError as e:
        print(f"Error al parsear fechas de viaje: {e}")
        raise
    resultado = []
    for oferta in ofertas:
        try:
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
        except ValueError as e:
            print(f"Error al parsear fechas de la oferta {oferta}: {e}")
            continue
        inicio_solapamiento = max(fecha_inicio_viaje, fecha_inicio_oferta)
        fin_solapamiento = min(fecha_fin_viaje, fecha_fin_oferta)
        if inicio_solapamiento <= fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days + 1
            resultado.append({
                "oferta": oferta,
                "dias_en_oferta": dias_en_oferta
            })
    return resultado


def obtener_habitacion(nombre_hotel, nombre_habitacion):
    try:
        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
        habitacion = Habitacion.objects.get(hotel=hotel, tipo=nombre_habitacion)
        return habitacion
    except ObjectDoesNotExist:
        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{nombre_habitacion}'.")
        return None


def obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre):
    try:
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
        ofertas = Oferta.objects.filter(
            hotel=hotel,
            tipo_habitacion=habitacion_nombre,
            disponible=True
        )
        ofertas_validas = []
        for oferta in ofertas:
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
            if fecha_inicio_viaje <= fecha_fin_oferta and fecha_fin_viaje >= fecha_inicio_oferta:
                ofertas_validas.append(oferta)
        return ofertas_validas
    except ObjectDoesNotExist:
        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{habitacion_nombre}'.")
        return []
    except ValueError as e:
        print(f"Error al parsear las fechas: {e}")
        return []


def recalcular_precio_y_costo(reserva):
    habitaciones_reserva = HabitacionReserva.objects.filter(reserva=reserva)
    precio_total = 0
    for habitacion_reserva in habitaciones_reserva:
        cant_adultos = habitacion_reserva.adultos
        habitacion_nombre = habitacion_reserva.habitacion_nombre
        fecha_viaje = habitacion_reserva.fechas_viaje
        nombre_hotel = reserva.hotel.hotel_nombre
        habitacion = obtener_habitacion(nombre_hotel, habitacion_nombre)
        ofertas = obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre)
        if habitacion_reserva.ninos == 1:
            nino1 = 1; nino2 = 0
        elif habitacion_reserva.ninos == 2:
            nino1 = 1; nino2 = 1
        else:
            nino1 = 0; nino2 = 0
        if habitacion and ofertas:
            dias_oferta = calcular_dias_por_oferta(ofertas, fecha_viaje)
            for result in dias_oferta:
                precio_total += calcula_precio(cant_adultos, nino1, nino2, result["oferta"], habitacion, result["dias_en_oferta"])
    return precio_total

# -------------------------------------------------------------------------------- #


# ---------------------------------------- PASAJEROS ---------------------------------------- #

@manager_required
@login_required
def listar_pasajeros(request):
    query = request.GET.get('q')
    pasajeros = Pasajero.objects.all()
    
    if query:
        pasajeros = pasajeros.filter(nombre__icontains=query)
        
    paginator = Paginator(pasajeros, 10)  # Mostrar 10 pasajeros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'backoffice/pasajeros/listar_pasajeros.html', {'page_obj': page_obj, 'query': query})

@manager_required
@login_required
def crear_pasajero(request):
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('backoffice:listar_pasajeros')
    else:
        form = PasajeroForm()
    return render(request, 'backoffice/pasajeros/editar_pasajero.html', {'form': form})

@manager_required
@login_required
def editar_pasajero(request, pk):
    pasajero = get_object_or_404(Pasajero, pk=pk)
    if request.method == 'POST':
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            form.save()
            return redirect('backoffice:listar_pasajeros')
    else:
        form = PasajeroForm(instance=pasajero)
    return render(request, 'backoffice/pasajeros/editar_pasajero.html', {'form': form})

@manager_required
@login_required
def eliminar_pasajero(request, pk):
    pasajero = get_object_or_404(Pasajero, pk=pk)
    if request.method == 'POST':
        pasajero.delete()
        return redirect('backoffice:listar_pasajeros')
    return render(request, 'backoffice/pasajeros/eliminar_pasajero.html', {'pasajero': pasajero})



# -------------------------------------------------------------------------------- #


# ---------------------------------------- OFERTAS ESPECIALES ---------------------------------------- #


# Listar Ofertas Especiales
@manager_required
@login_required
def listar_ofertas_especiales(request):
    query = request.GET.get('q', '')
    # Filtrar ofertas por nombre o código si hay una consulta
    ofertas_especiales = OfertasEspeciales.objects.filter(nombre__icontains=query) | OfertasEspeciales.objects.filter(codigo__icontains=query) if query else OfertasEspeciales.objects.all()
    context = {
        'ofertas_especiales': ofertas_especiales,
        'query': query
    }
    return render(request, 'backoffice/ofertas_especiales/listar_ofertas_especiales.html', context)

# Crear Oferta Especial
@manager_required
@login_required
def crear_oferta_especial(request):
    if request.method == 'POST':
        # Recibir datos directamente del request POST sin usar formularios de Django
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        tipo = request.POST.get('tipo')
        disponible = request.POST.get('disponible') == 'on'
        
        # Crear y guardar nueva oferta
        oferta = OfertasEspeciales(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            tipo=tipo,
            disponible=disponible
        )
        oferta.save()
        messages.success(request, 'Oferta especial creada exitosamente.')
        return redirect('backoffice:listar_ofertas_especiales')
    return render(request, 'backoffice/ofertas_especiales/editar_oferta_especial.html')

# Editar Oferta Especial
@manager_required
@login_required
def editar_oferta_especial(request, pk):
    oferta = get_object_or_404(OfertasEspeciales, pk=pk)
    if request.method == 'POST':
        # Recibir datos directamente del request POST sin usar formularios de Django
        oferta.codigo = request.POST.get('codigo')
        oferta.nombre = request.POST.get('nombre')
        oferta.descripcion = request.POST.get('descripcion')
        oferta.tipo = request.POST.get('tipo')
        oferta.disponible = request.POST.get('disponible') == 'on'
        oferta.save()
        messages.success(request, 'Oferta especial actualizada exitosamente.')
        return redirect('backoffice:listar_ofertas_especiales')
    return render(request, 'backoffice/ofertas_especiales/editar_oferta_especial.html', {'oferta': oferta})

# Eliminar Oferta Especial
@manager_required
@login_required
def eliminar_oferta_especial(request, pk):
    oferta = get_object_or_404(OfertasEspeciales, pk=pk)
    if request.method == 'POST':
        oferta.delete()
        messages.success(request, 'Oferta especial eliminada exitosamente.')
        return redirect('backoffice:listar_ofertas_especiales')
    return render(request, 'backoffice/ofertas_especiales/eliminar_oferta_especial.html', {'oferta': oferta})

# -------------------------------------------------------------------------------- #


# ---------------------------------------- RENTADORAS ---------------------------------------- #

@manager_required
@login_required
def listar_rentadoras(request):
    query = request.GET.get('q', '')
    rentadoras = Rentadora.objects.filter(nombre__icontains=query) if query else Rentadora.objects.all()
    return render(request, 'backoffice/rentadoras/listar_rentadoras.html', {'rentadoras': rentadoras, 'query': query})

@manager_required
@login_required
def crear_rentadora(request):
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        proveedor_id = request.POST.get('proveedor')
        proveedor = get_object_or_404(Proveedor, id=proveedor_id)

        Rentadora.objects.create(nombre=nombre, proveedor=proveedor)
        return redirect('backoffice:listar_rentadoras')

    return render(request, 'backoffice/rentadoras/crear_rentadora.html', {'proveedores': proveedores})

@manager_required
@login_required
def editar_rentadora(request, rentadora_id):
    rentadora = get_object_or_404(Rentadora, id=rentadora_id)
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        rentadora.nombre = request.POST.get('nombre')
        proveedor_id = request.POST.get('proveedor')
        rentadora.proveedor = get_object_or_404(Proveedor, id=proveedor_id)
        rentadora.save()
        return redirect('backoffice:listar_rentadoras')

    return render(request, 'backoffice/rentadoras/editar_rentadora.html', {'rentadora': rentadora, 'proveedores': proveedores})

@manager_required
@login_required
def eliminar_rentadora(request, rentadora_id):
    rentadora = get_object_or_404(Rentadora, id=rentadora_id)
    if request.method == 'POST':
        rentadora.delete()
        return redirect('backoffice:listar_rentadoras')
    return render(request, 'backoffice/rentadoras/eliminar_rentadora.html', {'rentadora': rentadora})

# -------------------------------------------------------------------------------- #
# ---------------------------------------- CATEGORIAS ---------------------------------------- #
@manager_required
@login_required
def listar_categorias(request):
    query = request.GET.get('q', '')
    categorias = Categoria.objects.filter(nombre__icontains=query) if query else Categoria.objects.all()
    return render(request, 'backoffice/categorias/listar_categorias.html', {'categorias': categorias, 'query': query})

@manager_required
@login_required
def crear_categoria(request):
    rentadoras = Rentadora.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        gasolina = request.POST.get('gasolina')
        rentadora_id = request.POST.get('rentadora')
        rentadora = get_object_or_404(Rentadora, id=rentadora_id)

        Categoria.objects.create(nombre=nombre, gasolina=gasolina, rentadora=rentadora)
        return redirect('backoffice:listar_categorias')

    return render(request, 'backoffice/categorias/crear_categoria.html', {'rentadoras': rentadoras})

@manager_required
@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    rentadoras = Rentadora.objects.all()

    if request.method == 'POST':
        categoria.nombre = request.POST.get('nombre')
        categoria.gasolina = request.POST.get('gasolina')
        rentadora_id = request.POST.get('rentadora')
        categoria.rentadora = get_object_or_404(Rentadora, id=rentadora_id)
        categoria.save()
        return redirect('backoffice:listar_categorias')

    return render(request, 'backoffice/categorias/editar_categoria.html', {'categoria': categoria, 'rentadoras': rentadoras})

@manager_required
@login_required
def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        categoria.delete()
        return redirect('backoffice:listar_categorias')
    return render(request, 'backoffice/categorias/eliminar_categoria.html', {'categoria': categoria})

# -------------------------------------------------------------------------------- #
# ---------------------------------------- CATEGORIAS ---------------------------------------- #
@manager_required
@login_required
def listar_modelos_autos(request):
    query = request.GET.get('q', '')
    modelos = ModeloAuto.objects.filter(nombre__icontains=query) if query else ModeloAuto.objects.all()
    return render(request, 'backoffice/modelos_autos/listar_modelos_autos.html', {'modelos': modelos, 'query': query})

@manager_required
@login_required
def crear_modelo_auto(request):
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        foto = request.FILES.get('foto')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, id=categoria_id)

        ModeloAuto.objects.create(nombre=nombre, descripcion=descripcion, foto=foto, categoria=categoria)
        return redirect('backoffice:listar_modelos_autos')

    return render(request, 'backoffice/modelos_autos/crear_modelo_auto.html', {'categorias': categorias})

@manager_required
@login_required
def editar_modelo_auto(request, modelo_id):
    modelo = get_object_or_404(ModeloAuto, id=modelo_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        modelo.nombre = request.POST.get('nombre')
        modelo.descripcion = request.POST.get('descripcion')
        modelo.foto = request.FILES.get('foto') or modelo.foto
        categoria_id = request.POST.get('categoria')
        modelo.categoria = get_object_or_404(Categoria, id=categoria_id)
        modelo.save()
        return redirect('backoffice:listar_modelos_autos')

    return render(request, 'backoffice/modelos_autos/editar_modelo_auto.html', {'modelo': modelo, 'categorias': categorias})

@manager_required
@login_required
def eliminar_modelo_auto(request, modelo_id):
    modelo = get_object_or_404(ModeloAuto, id=modelo_id)
    if request.method == 'POST':
        modelo.delete()
        return redirect('backoffice:listar_modelos_autos')
    return render(request, 'backoffice/modelos_autos/eliminar_modelo_auto.html', {'modelo': modelo})


# -------------------------------------------------------------------------------- #
# ---------------------------------------- LOCATIONS ---------------------------------------- #
@manager_required
@login_required
def listar_locations(request):
    query = request.GET.get('q', '')
    locations = Location.objects.filter(nombre__icontains=query) if query else Location.objects.all()
    return render(request, 'backoffice/locations/listar_locations.html', {'locations': locations, 'query': query})

@manager_required
@login_required
def crear_location(request):
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        pais = request.POST.get('pais')
        nomenclatura = request.POST.get('nomenclatura')
        es_aeropuerto = request.POST.get('es_aeropuerto') == 'on'
        disponibilidad_carros = request.POST.get('disponibilidad_carros')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, id=categoria_id)

        Location.objects.create(
            nombre=nombre,
            pais=pais,
            nomenclatura=nomenclatura,
            es_aeropuerto=es_aeropuerto,
            disponibilidad_carros=disponibilidad_carros,
            categoria=categoria
        )
        return redirect('backoffice:listar_locations')

    return render(request, 'backoffice/locations/crear_location.html', {'categorias': categorias})

@manager_required
@login_required
def editar_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        location.nombre = request.POST.get('nombre')
        location.pais = request.POST.get('pais')
        location.nomenclatura = request.POST.get('nomenclatura')
        location.es_aeropuerto = request.POST.get('es_aeropuerto') == 'on'
        location.disponibilidad_carros = request.POST.get('disponibilidad_carros')
        categoria_id = request.POST.get('categoria')
        location.categoria = get_object_or_404(Categoria, id=categoria_id)
        location.save()
        return redirect('backoffice:listar_locations')

    return render(request, 'backoffice/locations/editar_location.html', {'location': location, 'categorias': categorias})

@manager_required
@login_required
def eliminar_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    if request.method == 'POST':
        location.delete()
        return redirect('backoffice:listar_locations')
    return render(request, 'backoffice/locations/eliminar_location.html', {'location': location})

# ------------------------------------------------------------------------------------------------------------ #
# ---------------------------------------- CERTIFICADOS DE VACACIONES ---------------------------------------- #

@manager_required
@login_required
def listar_certificados(request):
    query = request.GET.get('q', '')
    certificados = CertificadoVacaciones.objects.filter(nombre__icontains=query) if query else CertificadoVacaciones.objects.all()
    return render(request, 'backoffice/certificado_vacaciones/listar_certificados.html', {'certificados': certificados, 'query': query})

@manager_required
@login_required
def crear_certificado(request):
    pasajeros = Pasajero.objects.all()
    opciones = OpcionCertificado.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        es_solo_adultos = request.POST.get('es_solo_adultos') == 'on'
        pasajero_id = request.POST.get('pasajero')
        pasajero = get_object_or_404(Pasajero, id=pasajero_id)

        # Crear el certificado de vacaciones
        certificado = CertificadoVacaciones.objects.create(
            nombre=nombre,
            es_solo_adultos=es_solo_adultos,
            pasajero=pasajero
        )

        # Añadir las opciones seleccionadas
        opciones_ids = request.POST.getlist('opciones')
        for opcion_id in opciones_ids:
            opcion = get_object_or_404(OpcionCertificado, id=opcion_id)
            certificado.opciones.add(opcion)

        return redirect('backoffice:listar_certificados')

    return render(request, 'backoffice/certificado_vacaciones/crear_certificado.html', {'pasajeros': pasajeros, 'opciones': opciones})

@manager_required
@login_required
def editar_certificado(request, certificado_id):
    certificado = get_object_or_404(CertificadoVacaciones, id=certificado_id)
    pasajeros = Pasajero.objects.all()
    opciones = OpcionCertificado.objects.all()

    if request.method == 'POST':
        certificado.nombre = request.POST.get('nombre')
        certificado.es_solo_adultos = request.POST.get('es_solo_adultos') == 'on'
        
        pasajero_id = request.POST.get('pasajero')
        certificado.pasajero = get_object_or_404(Pasajero, id=pasajero_id)
        
        # Actualizar las opciones seleccionadas
        opciones_ids = request.POST.getlist('opciones')
        certificado.opciones.clear()  # Limpiar las opciones actuales
        for opcion_id in opciones_ids:
            opcion = get_object_or_404(OpcionCertificado, id=opcion_id)
            certificado.opciones.add(opcion)

        certificado.save()
        return redirect('backoffice:listar_certificados')

    return render(request, 'backoffice/certificado_vacaciones/editar_certificado.html', {'certificado': certificado, 'pasajeros': pasajeros, 'opciones': opciones})

@manager_required
@login_required
def eliminar_certificado(request, certificado_id):
    certificado = get_object_or_404(CertificadoVacaciones, id=certificado_id)
    if request.method == 'POST':
        certificado.delete()
        return redirect('backoffice:listar_certificados')
    return render(request, 'backoffice/certificado_vacaciones/eliminar_certificado.html', {'certificado': certificado})

# ------------------------------------------------------------------------------------------------------------ #
# ---------------------------------------- OPCIONES DE CERTIFICADOS ---------------------------------------- #
@manager_required
@login_required
def listar_opciones_certificado(request):
    query = request.GET.get('q', '')
    opciones = OpcionCertificado.objects.filter(nombre__icontains=query) if query else OpcionCertificado.objects.all()
    return render(request, 'backoffice/opciones_certificado/listar_opciones_certificado.html', {'opciones': opciones, 'query': query})

@manager_required
@login_required
def crear_opcion_certificado(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')
        foto = request.FILES.get('foto')

        OpcionCertificado.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            foto=foto
        )
        return redirect('backoffice:listar_opciones_certificado')

    return render(request, 'backoffice/opciones_certificado/crear_opcion_certificado.html')

@manager_required
@login_required
def editar_opcion_certificado(request, opcion_id):
    opcion = get_object_or_404(OpcionCertificado, id=opcion_id)

    if request.method == 'POST':
        opcion.nombre = request.POST.get('nombre')
        opcion.descripcion = request.POST.get('descripcion')
        opcion.categoria = request.POST.get('categoria')
        if 'foto' in request.FILES:
            opcion.foto = request.FILES['foto']
        opcion.save()
        return redirect('backoffice:listar_opciones_certificado')

    return render(request, 'backoffice/opciones_certificado/editar_opcion_certificado.html', {'opcion': opcion})

@manager_required
@login_required
def eliminar_opcion_certificado(request, opcion_id):
    opcion = get_object_or_404(OpcionCertificado, id=opcion_id)
    if request.method == 'POST':
        opcion.delete()
        return redirect('backoffice:listar_opciones_certificado')
    return render(request, 'backoffice/opciones_certificado/eliminar_opcion_certificado.html', {'opcion': opcion})

# -------------------------------------------------------------------------------------------------#
# ---------------------------------------- TASAS DE CAMBIO ----------------------------------------#
@manager_required
@login_required
def listar_tasas_cambio(request):
    tasas_cambio = TasaCambio.objects.all()
    return render(request, 'backoffice/tasas_cambio/listar_tasas_cambio.html', {'tasas_cambio': tasas_cambio})

@manager_required
@login_required
def crear_tasa_cambio(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        tasa_cup = request.POST.get('tasa_cup')
        tasa_mlc = request.POST.get('tasa_mlc')
        activa = request.POST.get('activa') == 'true'

        # Crear una nueva tasa de cambio
        nueva_tasa = TasaCambio(
            tasa_cup=tasa_cup,
            tasa_mlc=tasa_mlc,
            activa=activa
        )
        nueva_tasa.save()
        return redirect('backoffice:listar_tasas_cambio')

    return render(request, 'backoffice/tasas_cambio/crear_tasa_cambio.html')

@manager_required
@login_required
def editar_tasa_cambio(request, tasa_id):
    tasa_cambio = get_object_or_404(TasaCambio, id=tasa_id)

    if request.method == 'POST':
        # Capturar los datos del formulario
        tasa_cambio.tasa_cup = request.POST.get('tasa_cup')
        tasa_cambio.tasa_mlc = request.POST.get('tasa_mlc')
        tasa_cambio.activa = request.POST.get('activa') == 'true'

        # Guardar los cambios
        tasa_cambio.save()
        return redirect('backoffice:listar_tasas_cambio')

    return render(request, 'backoffice/tasas_cambio/editar_tasa_cambio.html', {'tasa_cambio': tasa_cambio})

@manager_required
@login_required
def eliminar_tasa_cambio(request, tasa_id):
    tasa_cambio = get_object_or_404(TasaCambio, pk=tasa_id)
    if request.method == 'POST':
        tasa_cambio.delete()
        return redirect('backoffice:listar_tasas_cambio')
    return render(request, 'backoffice/tasas_cambio/eliminar_tasa_cambio.html', {'tasa_cambio': tasa_cambio})

# =========================================================================================== #
# ---------------------------------------- TRASLADOS ---------------------------------------- #
# =========================================================================================== #

@login_required
def listar_traslados(request):
    query = request.GET.get('q')
    traslados_list = Traslado.objects.all()

    if query:
        traslados_list = traslados_list.filter(
            transportista__nombre__icontains=query
        ) | traslados_list.filter(
            origen__nombre__icontains=query
        ) | traslados_list.filter(
            destino__nombre__icontains=query
        )

    paginator = Paginator(traslados_list, 10)  # 10 traslados por página
    page_number = request.GET.get('page')
    traslados = paginator.get_page(page_number)

    return render(request, 'backoffice/traslados/listar_traslados.html', {
        'traslados': traslados,
        'query': query,
    })


@manager_required
@login_required
def crear_traslado(request):
    if request.method == 'POST':
        transportista_id = request.POST.get('transportista')
        origen_id = request.POST.get('origen')
        destino_id = request.POST.get('destino')
        vehiculo_id = request.POST.get('vehiculo')
        costo = request.POST.get('costo')

        # Crear traslado
        Traslado.objects.create(
            transportista_id=transportista_id,
            origen_id=origen_id,
            destino_id=destino_id,
            vehiculo_id=vehiculo_id,
            costo=costo
        )
        return redirect('backoffice:listar_traslados')

    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()

    return render(request, 'backoffice/traslados/crear_traslado.html', {
        'transportistas': transportistas,
        'ubicaciones': ubicaciones,
        'vehiculos': vehiculos
    })

@manager_required
@login_required
def editar_traslado(request, traslado_id):
    traslado = get_object_or_404(Traslado, id=traslado_id)

    if request.method == 'POST':
        traslado.transportista_id = request.POST.get('transportista')
        traslado.origen_id = request.POST.get('origen')
        traslado.destino_id = request.POST.get('destino')
        traslado.vehiculo_id = request.POST.get('vehiculo')
        traslado.costo = request.POST.get('costo')
        traslado.save()
        return redirect('backoffice:listar_traslados')

    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()

    return render(request, 'backoffice/traslados/editar_traslado.html', {
        'traslado': traslado,
        'transportistas': transportistas,
        'ubicaciones': ubicaciones,
        'vehiculos': vehiculos
    })


@manager_required
@login_required
def eliminar_traslado(request, traslado_id):
    traslado = get_object_or_404(Traslado, pk=traslado_id)
    if request.method == 'POST':
        traslado.delete()
        return redirect('backoffice:listar_traslados')
    return render(request, 'backoffice/traslados/eliminar_traslado.html', {'traslado': traslado})


# =========================================================================================== #
# ----------------------------------- TRANSPORTISTAS ---------------------------------------- #
# =========================================================================================== #

@manager_required
@login_required
def listar_transportistas(request):
    transportistas = Transportista.objects.all()
    return render(request, 'backoffice/transportistas/listar_transportistas.html', {'transportistas': transportistas})

@manager_required
@login_required
def crear_transportista(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        Transportista.objects.create(nombre=nombre)
        return redirect('backoffice:listar_transportistas')
    return render(request, 'backoffice/transportistas/crear_transportista.html')

@manager_required
@login_required
def editar_transportista(request, transportista_id):
    transportista = get_object_or_404(Transportista, id=transportista_id)
    if request.method == 'POST':
        transportista.nombre = request.POST.get('nombre')
        transportista.save()
        return redirect('backoffice:listar_transportistas')
    return render(request, 'backoffice/transportistas/editar_transportista.html', {'transportista': transportista})

@manager_required
@login_required
def eliminar_transportista(request, transportista_id):
    transportista = get_object_or_404(Transportista, pk=transportista_id)
    if request.method == 'POST':
        transportista.delete()
        return redirect('backoffice:listar_transportistas')
    return render(request, 'backoffice/transportistas/eliminar_transportista.html', {'transportista': transportista})


# ======================================================================================== #
# ----------------------------------- UBICACIONES ---------------------------------------- #
# ======================================================================================== #
@login_required
def listar_ubicaciones(request):
    query = request.GET.get('q')
    ubicaciones_list = Ubicacion.objects.all()

    if query:
        ubicaciones_list = ubicaciones_list.filter(nombre__icontains=query)

    paginator = Paginator(ubicaciones_list, 10)  # 10 ubicaciones por página
    page_number = request.GET.get('page')
    ubicaciones = paginator.get_page(page_number)

    return render(request, 'backoffice/ubicaciones/listar_ubicaciones.html', {
        'ubicaciones': ubicaciones,
        'query': query,
    })


@manager_required
@login_required
def crear_ubicacion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        Ubicacion.objects.create(nombre=nombre)
        return redirect('backoffice:listar_ubicaciones')
    return render(request, 'backoffice/ubicaciones/crear_ubicacion.html')

@manager_required
@login_required
def editar_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id)
    if request.method == 'POST':
        ubicacion.nombre = request.POST.get('nombre')
        ubicacion.save()
        return redirect('backoffice:listar_ubicaciones')
    return render(request, 'backoffice/ubicaciones/editar_ubicacion.html', {'ubicacion': ubicacion})

@manager_required
@login_required
def eliminar_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    if request.method == 'POST':
        ubicacion.delete()
        return redirect('backoffice:listar_ubicaciones')
    return render(request, 'backoffice/ubicaciones/eliminar_ubicacion.html', {'ubicacion': ubicacion})


# ====================================================================================== #
# ----------------------------------- VEHICULOS ---------------------------------------- #
# ====================================================================================== #
@manager_required
@login_required
def listar_vehiculos(request):
    vehiculos = Vehiculo.objects.all()
    return render(request, 'backoffice/vehiculos/listar_vehiculos.html', {'vehiculos': vehiculos})

@manager_required
@login_required
def crear_vehiculo(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        capacidad_min = request.POST.get('capacidad_min')
        capacidad_max = request.POST.get('capacidad_max')
        foto = request.FILES.get('foto', None)

        # Crear y guardar el vehículo
        vehiculo = Vehiculo(
            tipo=tipo,
            capacidad_min=capacidad_min,
            capacidad_max=capacidad_max,
            foto=foto
        )
        vehiculo.save()

        return redirect('backoffice:listar_vehiculos')

    return render(request, 'backoffice/vehiculos/crear_vehiculo.html')

@manager_required
@login_required
def editar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        vehiculo.tipo = request.POST.get('tipo')
        vehiculo.capacidad_min = request.POST.get('capacidad_min')
        vehiculo.capacidad_max = request.POST.get('capacidad_max')

        # Manejo de la imagen subida
        if 'foto' in request.FILES:
            vehiculo.foto = request.FILES['foto']

        vehiculo.save()
        return redirect('backoffice:listar_vehiculos')
    
    return render(request, 'backoffice/vehiculos/editar_vehiculo.html', {'vehiculo': vehiculo})

@manager_required
@login_required
def eliminar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    if request.method == 'POST':
        vehiculo.delete()
        return redirect('backoffice:listar_vehiculos')
    
    return render(request, 'backoffice/vehiculos/eliminar_vehiculo.html', {'vehiculo': vehiculo})
