# booking/views.py

# Standard library imports
import json
from datetime import datetime, timedelta
import os
from decimal import Decimal

# Django imports
from django.shortcuts import get_object_or_404, render, redirect # type: ignore
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect # type: ignore
from django.db import transaction # type: ignore
from django.contrib import messages # type: ignore
from django.urls import reverse # type: ignore
from django.utils import timezone # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.core.serializers.json import DjangoJSONEncoder # type: ignore
from django.core.paginator import Paginator # type: ignore
from sympy import Q # type: ignore
from django.db.models import F # type: ignore

from django.db.models import Sum as DjangoSum # type: ignore
from decimal import Decimal, ROUND_HALF_UP


# Project-specific imports
from backoffice.models import (
    PoloTuristico, Hotel, Habitacion, Oferta, HabitacionOpcion, 
    Reserva, HabitacionReserva, Pasajero, OfertasEspeciales, Remesa,  
    TasaCambio,Ubicacion, Traslado, Transportista, Vehiculo
)
from usuarios.models import CustomUser
from backoffice.funciones_externas import (enviar_correo, calcular_precio_total_por_mes, contar_reservas_por_mes, ChequearIntervalos, obtener_ofertas_mas_baratas)
from .forms import PoloTuristicoForm, ProveedorForm, CadenaHoteleraForm, ReservaForm, PasajeroForm, HabitacionForm, OfertasEspecialesForm


@login_required
def check_session_status(request):
    # Si el usuario está autenticado, devuelve "active", de lo contrario "inactive"
    return JsonResponse({'status': 'active'})

# ================================================================================================== #
# ---------------------------------------- Sección: Dashboard -------------------------------------- #
# ================================================================================================== #
@login_required
def en_desarrollo(request):
    return render(request, 'booking/en_desarrollo.html')

@login_required
def en_mantenimiento(request):
    return render(request, 'booking/en_mantenimiento.html') 

# Vista para obtener los datos del dashboard de administración
@login_required
def admin_dashboard_data(request):    
    reservas = Reserva.objects.all()  # Obtener todas las reservas
    ofertas_especiales = OfertasEspeciales.objects.all()
    ganancias_totales = 0
    
    # Calcular las ganancias totales de todas las reservas
    for reserva in reservas:
        ganancias_totales += reserva.precio_total

    # Preparar los datos a enviar en formato JSON
    data = {
        'total_hotels': Hotel.objects.count(),  # Total de hoteles
        'total_rooms': Habitacion.objects.count(),  # Total de habitaciones
        'total_reservations': Reserva.objects.filter(estatus='confirmada').count(),  # Total de reservas confirmadas
        'recent_reservations': list(Reserva.objects.order_by('-fecha_reserva')[:5].values()),  # Reservas recientes
        'recent_hotels': list(Hotel.objects.order_by('-id')[:5].values()),  # Hoteles recientes
        'ganancias_totales': ganancias_totales,  # Ganancias totales
        'ofertas_especiales': ofertas_especiales
    }
    return JsonResponse(data)

@login_required
def user_dashboard(request):
    usuario = request.user

    if not usuario.agencia.strip():
        messages.error(request, "El nombre de usuario no está definido.")
        return redirect('home')

    reservas = Reserva.objects.filter(nombre_usuario__iexact=usuario.agencia)
    remesas = Remesa.objects.filter(reserva__nombre_usuario__iexact=usuario.agencia, reserva__tipo='remesas')

    ofertas_especiales = OfertasEspeciales.objects.filter(disponible=True)
    total_hotels = Hotel.objects.count()
    total_rooms = Habitacion.objects.count()
    recent_hotels = Hotel.objects.order_by('-id')[:5]
    cant_usuarios = CustomUser.objects.count()

    total_reservations = reservas.count()
    estados_reservas = {
        'solicitada': reservas.filter(estatus='solicitada').count(),
        'pendiente': reservas.filter(estatus='pendiente').count(),
        'confirmada': reservas.filter(estatus='confirmada').count(),
        'modificada': reservas.filter(estatus='modificada').count(),
        'ejecutada': reservas.filter(estatus='ejecutada').count(),
        'cancelada': reservas.filter(estatus='cancelada').count(),
        'reembolsada': reservas.filter(estatus='reembolsada').count(),
    }

    reservas_por_cobrar = reservas.filter(cobrada=False).count()
    reservas_por_pagar = reservas.filter(pagada=False).count()
    reservas_recientes = reservas.order_by('-fecha_reserva')[:5]
    ganancias_totales = sum(float(reserva.precio_total) for reserva in reservas)

    precio_total_por_mes = calcular_precio_total_por_mes(reservas)
    cant_reservas_por_mes = contar_reservas_por_mes(reservas)

    today = datetime.now()
    labels = []
    reservas_data = []
    ingresos_data = []
    deudas_data = []

    for i in range(12):
        month = (today.month - i - 1) % 12 + 1
        year = today.year if month <= today.month else today.year - 1

        labels.insert(0, datetime(year, month, 1).strftime('%b'))
        reservas_mes = reservas.filter(fecha_reserva__year=year, fecha_reserva__month=month)

        reservas_data.insert(0, reservas_mes.count())
        ingresos_mes = float(reservas_mes.aggregate(DjangoSum('precio_total'))['precio_total__sum'] or 0)
        deudas_mes = float(reservas_mes.filter(cobrada=False).aggregate(DjangoSum('precio_total'))['precio_total__sum'] or 0)

        ingresos_data.insert(0, ingresos_mes)
        deudas_data.insert(0, deudas_mes)

    context = {
        'total_reservations': total_reservations,
        'estados_reservas': estados_reservas,
        'reservas_por_cobrar': reservas_por_cobrar,
        'reservas_por_pagar': reservas_por_pagar,
        'reservas_recientes': reservas_recientes,
        'ganancias_totales': ganancias_totales,
        'precio_total_por_mes': precio_total_por_mes,
        'cant_reservas_por_mes': cant_reservas_por_mes,
        'total_hotels': total_hotels,
        'total_rooms': total_rooms,
        'recent_hotels': recent_hotels,
        'cant_usuarios': cant_usuarios,
        'ofertas_especiales': ofertas_especiales,
        'labels': labels,
        'reservas_data': reservas_data,
        'ingresos_data': ingresos_data,
        'deudas_data': deudas_data,
    }

    return render(request, 'booking/user_dashboard.html', context)

@login_required
def perfil_cliente(request):
    usuario = request.user

    if request.method == 'POST':
        # Obtener los datos del formulario
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')        
        nombre_dueno = request.POST.get('nombre_dueno')        
        telefono_dueno = request.POST.get('telefono_dueno')        
        fee_hotel = request.POST.get('fee_hotel')
        tipo_fee_hotel = request.POST.get('tipo_fee_hotel')
        fee_carro = request.POST.get('fee_carro')  
        tipo_fee_carro = request.POST.get('tipo_fee_carro')
        fee_tarara = request.POST.get('fee_tarara')
        tipo_fee_tarara = request.POST.get('tipo_fee_tarara')

        # Actualizar los datos del usuario
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.email = email
        usuario.telefono = telefono
        usuario.direccion = direccion
        usuario.nombre_dueno = nombre_dueno
        usuario.telefono_dueno = telefono_dueno
        usuario.fee_hotel = fee_hotel
        usuario.tipo_fee_hotel = tipo_fee_hotel
        usuario.fee_carro = fee_carro
        usuario.tipo_fee_carro = tipo_fee_carro
        usuario.fee_tarara = fee_tarara
        usuario.tipo_fee_tarara = tipo_fee_tarara

        # Si se subió una nueva imagen de logo
        if 'logo' in request.FILES:
            usuario.logo = request.FILES['logo']

        # Guardar cambios
        try:
            usuario.save()
            messages.success(request, 'Perfil guardado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')

        return redirect('booking:perfil_cliente')  # Asegúrate de que 'perfil_cliente' es el nombre correcto en tus URLs

    # Renderiza la plantilla con los datos del usuario
    context = {
        'user': usuario,
    }
    return render(request, 'booking/perfil_cliente.html', context)

# Vista para el dashboard de hoteles
@login_required
def hotel_dashboard(request):
    destinos = PoloTuristico.objects.all()  # Obtener todos los destinos turísticos
    context = {
        'destinos': destinos,
    }    
    return render(request, 'booking/hotel/dashboard.html', context)

# ================================================================================================== #
# ---------------------------------------- Sección: Hotel Búsqueda --------------------------------- #
# ================================================================================================== #

# Vista para la búsqueda de hoteles
@login_required
def hotel_search(request):
    destinos = PoloTuristico.objects.all()  # Obtener todos los destinos turísticos
    context = {
        'destinos': destinos,
    }
    return render(request, 'booking/hotel_search.html', context)

# Vista para mostrar los resultados de la búsqueda de hoteles
@login_required
def hotel_results(request):
    # Obtener los parámetros de búsqueda desde la solicitud GET
    destino = request.GET.get('destino', '')
    fechas_viaje = request.GET.get('fechas_viaje', '')
    
    try:
        cant_habitaciones = int(request.GET.get('habitaciones', 1))
        cant_adultos = int(request.GET.get('adultos', 1))
        cant_ninos = int(request.GET.get('ninos', 0))
    except ValueError:
        messages.error(request, "Los valores de habitaciones, adultos o niños no son válidos.")
        return redirect('hotel_search')

    info_habitaciones = request.GET.get('info_habitaciones', '')

    # Procesar la información de habitaciones si está disponible
    try:
        info_habitaciones = json.loads(info_habitaciones) if info_habitaciones else {'totalNinos': cant_ninos}
    except json.JSONDecodeError:
        messages.error(request, "La información de habitaciones no es válida.")
        return redirect('hotel_search')

    # Separar fechas_viaje en fecha_checkin y fecha_checkout
    fecha_checkin = ''
    fecha_checkout = ''
    if fechas_viaje:
        fechas = fechas_viaje.split(' - ')
        if len(fechas) == 2:
            fecha_checkin = fechas[0]
            fecha_checkout = fechas[1]

    # Calcular la cantidad de días de la reserva
    cantidad_dias_reserva = 0
    if fecha_checkin and fecha_checkout:
        try:
            checkin_date = datetime.strptime(fecha_checkin, '%Y-%m-%d')
            checkout_date = datetime.strptime(fecha_checkout, '%Y-%m-%d')
            cantidad_dias_reserva = (checkout_date - checkin_date).days
        except ValueError:
            messages.error(request, "Las fechas de check-in o check-out no son válidas.")
            return redirect('hotel_search')

    hoteles = Hotel.objects.all()

    # Filtrar los hoteles según el destino seleccionado
    if destino and destino != 'todos-los-destinos':
        hoteles = hoteles.filter(polo_turistico__nombre__iexact=destino.replace('-', ' '))

    # Filtrar los hoteles según la política de admisión de niños
    if info_habitaciones.get('totalNinos', 0) > 0:
        hoteles = hoteles.filter(solo_adultos=False)
    
    # Obtener el diccionario de ofertas más baratas
    cant_personas = cant_adultos + cant_ninos    
    ofertas_mas_baratas = obtener_ofertas_mas_baratas(request, hoteles, cant_personas, cantidad_dias_reserva, fechas_viaje)

   
    # Preparar el contexto para la plantilla
    context = {
        'destinos': PoloTuristico.objects.all(),
        'hoteles': hoteles,
        'fecha_checkin': fecha_checkin,
        'fecha_checkout': fecha_checkout,
        'cant_habitaciones': cant_habitaciones,
        'cant_adultos': cant_adultos,
        'cant_ninos': cant_ninos,
        'destino': destino,
        'info_habitaciones': info_habitaciones,
        'fechas_viaje': fechas_viaje,
        'ofertas_mas_baratas': ofertas_mas_baratas
    }

    return render(request, 'booking/hotel/hotel_results.html', context)

# ================================================================================================== #
# -------------------------------------- Sección: Hotel Detalles ----------------------------------- #
# ================================================================================================== #

# Vista para mostrar los detalles de un hotel específico
@login_required
def hotel_detalle(request, hotel_id):
    #print('Entro a: hotel_detalle')

    hotel = get_object_or_404(Hotel, id=hotel_id)  # Obtener el hotel o devolver 404 si no existe
    habitaciones = Habitacion.objects.filter(hotel=hotel)  # Obtener las habitaciones del hotel
    ofertas = Oferta.objects.filter(hotel=hotel)  # Obtener las ofertas del hotel      
    plan_alimenticio = hotel.plan_alimenticio
    
    usuario_logueado = request.user  # Esto devuelve el usuario que está logueado en la sesión
    fee_hotel = usuario_logueado.fee_hotel
    tipo_fee_hotel = usuario_logueado.tipo_fee_hotel
    fee_nino = usuario_logueado.fee_nino
   
    
    # Validación: Obtener y validar la información de la solicitud GET
    try:
        cant_habitaciones = int(request.GET.get('habitaciones', 0))
        cant_adultos = int(request.GET.get('adultos', 0))
        cant_ninos = int(request.GET.get('ninos', 0))
        info_habitaciones = json.loads(request.GET.get('info_habitaciones', '{}'))
    except (ValueError, json.JSONDecodeError):
        messages.error(request, "Los datos de la solicitud no son válidos.")
        return redirect('hotel_search')

    fechas_viaje = request.GET.get('fechas_viaje', '')
    num_habitaciones = int(info_habitaciones.get('numHabitaciones', 0))
    
    habitaciones_data = []

    # Procesar cada habitación
    for i in range(num_habitaciones):
        habitacion_info = info_habitaciones['datosHabitaciones'][i]
        opciones = get_opciones_habitacion(habitaciones, ofertas, habitacion_info, fechas_viaje, tipo_fee_hotel, fee_hotel, fee_nino)
               
        habitaciones_data.append({
            'habitacion': f'Habitación {i+1}',
            'adultos': habitacion_info['adultos'],
            'ninos': habitacion_info['ninos'],
            'total_pax': f"{habitacion_info['adultos']} + {habitacion_info['ninos']}",
            'opciones': opciones,
            'cant_adultos': habitacion_info['adultos'],
            'cant_ninos': habitacion_info['ninos'],
            'fechas_viaje': fechas_viaje,
            # Añadimos precio_sin_fee y total_fee si lo deseas mostrar
        })
    
    # Preparar el contexto para la plantilla
    context = {
        'hotel': hotel,
        'habitaciones_data': habitaciones_data,
        'info_habitaciones': info_habitaciones,
        'plan_alimenticio': plan_alimenticio,
        'destinos': PoloTuristico.objects.all(),            
        'fechas_viaje': fechas_viaje,
    }
    return render(request, 'booking/hotel/hotel_detalle.html', context)

def calcular_cantidad_noches(rango_fechas):
    #print('Entro a: calcular_cantidad_noches')
    
    # Separar las fechas
    fecha_inicio_str, fecha_fin_str = rango_fechas.split(" - ")
    
    # Convertir las fechas a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    
    # Calcular la diferencia de días
    dias = (fecha_fin - fecha_inicio).days
    
    return dias

# Función auxiliar para obtener las opciones de habitación
def get_opciones_habitacion(habitaciones, ofertas, habitacion_info, fechas_viaje, tipo_fee_hotel, fee_hotel, fee_nino):
    opciones = []

    for habitacion in habitaciones:
        try:
            cant_adultos = int(habitacion_info['adultos'])
            cant_ninos = int(habitacion_info['ninos'])
        except ValueError:
            print(f"Error en los valores de adultos o niños para la habitación {habitacion.id}")
            continue

        edades_ninos = habitacion_info.get('edadesNinos', [])
        nino1 = 1 if len(edades_ninos) > 0 else 0
        nino2 = 1 if len(edades_ninos) > 1 else 0

        try:
            # Calcular el precio según el tipo de habitación, cantidad de adultos, y niños
            precio, precio_sin_fee, total_fee = calcular_precios_por_tipo_habitacion(
                cant_adultos, nino1, nino2, fechas_viaje, ofertas, habitacion
            )
            
            # Calcular la cantidad de noches en el rango de fechas de viaje
            cantidad_noches = calcular_cantidad_noches(fechas_viaje)

            # Calcular el precio total según el tipo de fee del hotel (fijo o porcentaje)-----------------------------------------------------------------------
            if tipo_fee_hotel == "PAX":              
                
                precio += ((fee_hotel * cant_adultos) + (fee_nino * cant_ninos)) * cantidad_noches                
                
            elif tipo_fee_hotel == "Reserva":
                
                precio += fee_hotel
            
            else:
                
                precio += precio * fee_hotel / 100
            
        except ValueError as e:
            print(f"Error al calcular el precio para la habitación {habitacion.id}: {e}")
            precio = None

        opcion, _ = HabitacionOpcion.objects.get_or_create(
            habitacion=habitacion,
            nombre=habitacion.tipo,
            defaults={'descripcion': habitacion.descripcion, 'precio': precio}
        )

        if precio > 0:
            opciones.append({
                'id': opcion.id,
                'nombre': opcion.nombre,
                'descripcion': opcion.descripcion,
                'precio': precio if precio is not None else "No disponible",
                'precio_sin_fee': precio_sin_fee,
                'total_fee': total_fee,
                'destinos': PoloTuristico.objects.all(),
                'fechas_viaje': fechas_viaje,
            })

    return opciones

# Función auxiliar para calcular los días aplicables de una oferta
def calcular_dias_por_oferta(ofertas, fecha_viaje):
    #print('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
    #print('Entro a: calcular_dias_por_oferta(ofertas, fecha_viaje)')
    
    try:
        # Parsear las fechas de viaje        
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
        
        # Calculamos la cantidad de días
        cantidad_dias = (fecha_fin_viaje - fecha_inicio_viaje).days
        
        #print('---Parsear las fechas de viaje ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        #print(f"fecha_inicio_viaje: {fecha_inicio_viaje}")
        #print(f"   fecha_fin_viaje: {fecha_fin_viaje}")
        #print(f"     cantidad_dias: {cantidad_dias}") 
        
        
    except ValueError as e:
        print(f"Error al parsear fechas de viaje: {e}")
        raise

    resultado = []

    # Procesar cada oferta y calcular los días de solapamiento
    
    for oferta in ofertas:        
        #print(f"----------------- Oferta ----------------: {oferta.temporada}")
        try:
                       
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
            
            #print('---Procesar cada oferta y calcular los días de solapamiento---') 
            #print(f"fecha_inicio_oferta: {fecha_inicio_oferta}")
            #print(f"   fecha_fin_oferta: {fecha_fin_oferta}") 
          
        except ValueError as e:
            print(f"Error al parsear fechas de la oferta {oferta}: {e}")
            continue

        inicio_solapamiento = max(fecha_inicio_viaje, fecha_inicio_oferta)
        fin_solapamiento = min(fecha_fin_viaje, fecha_fin_oferta)
        #print('')
        #print('---Inicio y fin de solapamiento---') 
        #print(f"inicio_solapamiento: {inicio_solapamiento}")
        #print(f"   fin_solapamiento: {fin_solapamiento}")         
        dias_en_oferta = 0
        #print('--------------')
        #print(f"OUT If dias_en_oferta: {dias_en_oferta}") 

        if inicio_solapamiento < fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days
            if cantidad_dias == dias_en_oferta:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": True 
                })
            else:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": False
                })
                
            #print(f" IN If dias_en_oferta: {dias_en_oferta}") 
        
        elif inicio_solapamiento == fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days + 1
            if cantidad_dias == dias_en_oferta:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": True 
                })
            else:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": False
                })
            #print(f" IN If dias_en_oferta: {dias_en_oferta}") 
            
        #print('----- Resultado -----')
        #print(f"resultado: {resultado}")

    return resultado

# Función auxiliar para calcular el precio de una habitación según la oferta
def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion , cant_dias):
    
    #print('------------------------------')
    #print('Entro a: calcula_precio')
    
    # Imprimir valores
    #print(f"cant_adultos (Cantidad de adultos): {cant_adultos}")
    #print(f"nino1 (Primer niño): {nino1}")
    #print(f"nino2 (Segundo niño): {nino2}")
    #print(f"oferta (Oferta aplicada): {oferta}")
    #print(f"habitacion (Tipo de habitación): {habitacion}")
    #print(f"cant_dias (Cantidad de días de estadía): {cant_dias}")

    if not (0 <= cant_adultos <= 3):
        raise ValueError("La cantidad de adultos debe ser entre 0 y 3.")
    if nino1 not in [0, 1]:
        raise ValueError("nino1 debe ser 0 o 1.")
    if nino2 not in [0, 1]:
        raise ValueError("nino2 debe ser 0 o 1.")
    if nino2 == 1 and nino1 == 0:
        raise ValueError("No puede haber un nino2 sin un nino1.")

    # Inicializar variables
    precio_sin_fee = 0
    total_fee = 0
    cant_personas = cant_adultos + nino1 + nino2

    # Precios por tipo de habitación y personas
    J = float(oferta.doble)
    K = float(oferta.triple)
    L = float(oferta.sencilla)
    M = float(oferta.primer_nino)
    N = float(oferta.segundo_nino)
    O = float(oferta.un_adulto_con_ninos)
    P = float(oferta.primer_nino_con_un_adulto)
    Q = float(oferta.segundo_nino_con_un_adulto)

    fee_sencilla = float(oferta.fee_sencilla or 0)
    fee_doble = float(oferta.fee_doble or 0)
    fee_triple = float(oferta.fee_triple or 0)
    fee_primer_nino = float(oferta.fee_primer_nino or 0)
    fee_segundo_nino = float(oferta.fee_segundo_nino or 0)

    # para ajustar bien la cantidada de dias.
    cant_dias = cant_dias
    
    # Calcular el precio según la cantidad de adultos y niños
    if cant_adultos == 1:
        if nino1 == 0 and nino2 == 0:
            print('Entro Sencilla 1 adulto')
            precio_sin_fee = L * cant_dias
            total_fee = (L + fee_sencilla) * cant_dias
            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 0:
            print('Entro 1 adulto y 1 niño')
            precio_sin_fee = ((O + P) * cant_personas) * cant_dias
            
            if P > 0:
                # Si P es mayor que 0, se suma P y fee_primer_nino (El primer niño tiene un costo)
                valor_p = P + fee_doble
            elif P == 0 and fee_doble != 0:
                # Si P es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_p = 0
            else:
                # Si P es menor que 0, se usa un valor predeterminado negativo (No se permite el primer niño)
                valor_p = -999999999

            # Cálculo total de la tarifa
            total_fee = ((O + fee_doble) + valor_p) * cant_dias


            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 1:
            print('Entro 1 adulto y 2 niños')
            precio_sin_fee = ((O + P + Q) + 2) * cant_dias

            # Evaluación condicional para P
            if P > 0:
                # Si P es mayor que 0, se utiliza su valor normal
                valor_p = P
            elif P == 0:
                # Si P es igual a 0, el resultado será 0
                valor_p = 0
            else:
                # Si P es menor que 0, asignamos un valor predeterminado de penalización
                valor_p = -99999999

            # Evaluación condicional para Q
            if Q > 0:
                # Si Q es mayor que 0, se utiliza su valor normal
                valor_q = Q
            elif Q == 0:
                # Si Q es igual a 0, el resultado será 0
                valor_q = 0
            else:
                # Si Q es menor que 0, asignamos un valor predeterminado de penalización
                valor_q = -99999999

            # Cálculo total de la tarifa
            total_fee = ((O + valor_p + valor_q) + (fee_doble * 2) + fee_primer_nino) * cant_dias

                        
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')

    elif cant_adultos == 2:
        if nino1 == 0 and nino2 == 0:            
            #print('Entro Doble 2 adultos')
            #print('----------------------')
            #print(f"            J: {J}")
            #print(f"    fee_doble: {fee_doble}")
            #print(f"cant_personas: {cant_personas}")
            #print(f"    cant_dias: {cant_dias}")
            #print('----------------------')
            precio_sin_fee = ( J ) * cant_personas * cant_dias
            total_fee = (J + fee_doble) * cant_personas * cant_dias
            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 0:
            print('Entro 2 adultos y 1 niño')
            precio_sin_fee = (( J ) * cant_adultos + M ) * cant_dias
            
            if M > 0:
                # Si M es mayor que 0, se suma M y fee_primer_nino (El primer niño tiene un costo)
                valor_m = M + fee_primer_nino
            elif M == 0 and fee_primer_nino != 0:
                # Si M es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_m = 0
            else:
                # Si M es menor que 0, simplemente se usa M (No se permite el primer niño)
                valor_m = -999999999

            # Cálculo total de la tarifa
            total_fee = ((J + fee_doble) * cant_adultos + valor_m) * cant_dias                               
         
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 1:
            print('Entro 2 adultos y 2 niños')
            precio_sin_fee = (J * cant_adultos + M + N) * cant_dias
            
            # Evaluación condicional para M
            if M > 0:
                # Si M es mayor que 0, se suma M y fee_primer_nino (El primer niño tiene un costo)
                valor_m = M + fee_primer_nino
            elif M == 0 and fee_primer_nino != 0:
                # Si M es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_m = 0
            else:
                # Si M es menor que 0, asignamos el valor predeterminado de penalización
                valor_m = -99999999

            # Evaluación condicional para N
            if N > 0:
                # Si N es mayor que 0, se suma N y fee_segundo_nino (El segundo niño tiene un costo)
                valor_n = N + fee_segundo_nino
            elif N == 0 and fee_segundo_nino != 0:
                # Si N es igual a 0 y fee_segundo_nino no es 0, el resultado será 0 (El segundo niño es gratuito)
                valor_n = 0
            else:
                # Si N es menor que 0, asignamos el valor predeterminado de penalización
                valor_n = -99999999

            # Cálculo total de la tarifa
            total_fee = ((J + fee_doble) * cant_adultos + valor_m + valor_n) * cant_dias

                        
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')

    elif cant_adultos == 3:
        if nino1 == 0 and nino2 == 0:
            print('Entro Triple 3 adultos')
            precio_sin_fee = (K * cant_personas) * cant_dias
            total_fee = (K + fee_triple) * cant_personas * cant_dias
            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 0 and habitacion.admite_3_con_1:
            print('Entro 3 adultos y 1 niño')
            precio_sin_fee = (( K ) * cant_personas + M  ) * cant_dias
            # Evaluación condicional para M
            if M > 0:
                # Si M es mayor que 0, se suma M y fee_primer_nino (El primer niño tiene un costo)
                valor_m = M + fee_primer_nino
            elif M == 0 and fee_primer_nino != 0:
                # Si M es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_m = 0
            else:
                # Si M es menor que 0, asignamos un valor predeterminado de penalización
                valor_m = -99999999

            # Cálculo total de la tarifa
            total_fee = ((K + fee_triple) * cant_personas + valor_m) * cant_dias

                        
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')

    #---------------------------------------------------------
    """print('---------------------------------------------------------')
        
    if cant_adultos == 1:
        if nino1 == 0 and nino2 == 0:
            precio = (L + fee_sencilla) * cant_adultos
            
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
            
        elif nino1 == 1 and nino2 == 0:
            precio = (O + P) + (fee_doble * cant_personas)
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
            
        elif nino1 == 1 and nino2 == 1:
            precio = (O + P + Q) + (fee_doble * 2) + fee_primer_nino
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")


    elif cant_adultos == 2:
        if nino1 == 0 and nino2 == 0:
            precio = (J + fee_doble) * cant_personas
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
                
        elif nino1 == 1 and nino2 == 0:
            precio = (J + fee_doble) * cant_adultos + M + fee_primer_nino            
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
                
        elif nino1 == 1 and nino2 == 1:
            precio = (J + fee_doble) * cant_adultos + M + fee_primer_nino + N + fee_segundo_nino
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")

    elif cant_adultos == 3:
        if nino1 == 0 and nino2 == 0:
            precio = (K + fee_triple) * cant_adultos
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
                
        elif nino1 == 1 and nino2 == 0 and habitacion.admite_3_con_1:
            precio = (K + fee_triple) * cant_adultos + M + fee_primer_nino            
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2}, Admite 3 con 1 -> Precio: {precio}") """





    # Precio total
    precio_total = precio_sin_fee + total_fee
    
    precio_total = total_fee

    return precio_total, precio_sin_fee, total_fee

# Función auxiliar para calcular los precios por tipo de habitación
def calcular_precios_por_tipo_habitacion(cant_adultos, nino1, nino2, fecha_viaje, ofertas, habitacion):
    precio_total = 0
    precio_sin_fee_total = 0
    total_fee = 0
    ofertas_tipo = []

    for oferta in ofertas:
        if oferta.tipo_habitacion == habitacion.tipo and oferta.disponible:
            ofertas_tipo.append(oferta)

    resultado = calcular_dias_por_oferta(ofertas_tipo, fecha_viaje)
    #print('----- Entro a: calcular_precios_por_tipo_habitacion -----')
    #print(f"El Resltado aqui es: (resultado): {resultado}")

    precio_total = 0
    precio_sin_fee_total = 0  
    total_fee = 0
    
    for result in resultado:
        #print('-------------------------------------')
        #print(f" resul en itercacion: (result): {result}")
        
        oferta = result["oferta"]
        #print(f"oferta en itercacion: (oferta): {oferta}")
        
        dias_en_oferta = result["dias_en_oferta"]
        #print(f"  dias_en_oferta en itercacion: (dias_en_oferta): {dias_en_oferta}")
        #print('----- calcula_precio ------')
        
        precio, precio_sin_fee, fee = calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, dias_en_oferta)
        
        if result["completa"]:   
            #print('--------------------------------------------------- COMPLETA COMPLETA COMPLETA COMPLETA COMPLETA ---------------------------------------------------')     
            precio_total = precio
            precio_sin_fee_total = precio_sin_fee
            total_fee = fee
        
        if not result["completa"]:   
            #print('--------------------------------------------------- NOO COMPLETA NOO COMPLETANOO COMPLETANOO COMPLETA ---------------------------------------------------')     
            precio_total += precio
            precio_sin_fee_total += precio_sin_fee
            total_fee += fee
        
        #print(f"                precio_total en itercacion: (precio_total): {precio_total}")
        #print(f"precio_sin_fee_total en itercacion: (precio_sin_fee_total): {precio_sin_fee_total}")
        #print(f"                      total_fee en itercacion: (total_fee): {total_fee}")

    return precio_total, precio_sin_fee_total, total_fee

# Función auxiliar para obtener la descripción del plan alimenticio según el código
def get_plan_alimenticio(plan_code):

    #print('Entro a: get_plan_alimenticio')
    
    plan_dict = {
        'AI': 'Todo Incluido (AI)',
        'MAP': 'Alojamiento, Desayuno y Cena (MAP)',
        'CP': 'Alojamiento y Desayuno (CP)',
        'AP': 'Alojamiento, Desayuno, Almuerzo y Cena (AP)',
        'EP': 'Solo Alojamiento (EP)'
    }
    return plan_dict.get(plan_code, 'Solo Alojamiento (EP)')

# ================================================================================================== #
# ---------------------------- Sección: Hotel Pago y Reserva --------------------------------------- #
# ================================================================================================== #

# Vista para manejar el proceso de pago y reserva de un hotel
@login_required
def hotel_pago_reserva(request, hotel_id):
    
    hotel = get_object_or_404(Hotel, id=hotel_id)  # Obtener el hotel o devolver 404 si no existe
    
    # Captura de valores desde request.GET una sola vez
    destino = request.GET.get('destino', '')  
    fechas_viaje = request.GET.get('fechas_viaje', '')
    habitaciones = request.GET.get('habitaciones', '')
    adultos = request.GET.get('adultos', '')
    ninos = request.GET.get('ninos', '')
    info_habitaciones = request.GET.get('info_habitaciones', '{}')  # Captura info_habitaciones como un JSON
    
    # Decodificación de info_habitaciones (si es necesario)
    import json
    try:
        info_habitaciones_decoded = json.loads(info_habitaciones)
    except json.JSONDecodeError:
        info_habitaciones_decoded = {}  # En caso de error, asigna un diccionario vacío
    
    # Si es una solicitud GET
    if request.method == 'GET':
        context = {
            'destino': destino,
            'fechas_viaje': fechas_viaje,
            'habitaciones': habitaciones,
            'adultos': adultos,
            'ninos': ninos,
            'info_habitaciones': info_habitaciones_decoded,  # Decodificado si es necesario
        }
        return render(request, 'booking/hotel/hotel_pago_reserva.html', context)
    
    # Si es una solicitud POST
    #print('********************* ENTRO AL POST ****************************')
    habitaciones = []
    opciones_seleccionadas = []
    precio_total = 0

    # Procesar las opciones seleccionadas para cada habitación en el POST
    for key, value in request.POST.items():
        if key.startswith('opciones_habitacion_'):
            habitacion_index = int(key.split('_')[-1])
            
            try:
                opcion_id = int(value) if value else None
                
                if opcion_id:
                    opcion = HabitacionOpcion.objects.get(id=opcion_id)
                    precio_opcion = request.POST.get(f'precio_opcion_{habitacion_index}', '0')
                    
                    opciones_seleccionadas.append({
                        'habitacion_index': habitacion_index,
                        'opcion': {
                            'id': opcion.id,
                            'nombre': opcion.nombre,
                            'descripcion': opcion.descripcion,
                            'precio': precio_opcion,
                        },
                        'precio': float(precio_opcion) if precio_opcion.isdigit() else 0
                    })
                    precio_total += float(precio_opcion.replace(',', '.'))

                    
            except HabitacionOpcion.DoesNotExist:
                print(f"Error: No se encontró HabitacionOpcion con id {opcion_id}")
                
    # Procesar cada opción seleccionada
    for opcion_seleccionada in opciones_seleccionadas:
        habitacion_index = opcion_seleccionada['habitacion_index']
        nombre_habitacion = request.POST.get(f'habitacion_{habitacion_index}_nombre', '')
        num_adultos = int(request.POST.get(f'habitacion_{habitacion_index}_adultos', '0') or 0)
        num_ninos = int(request.POST.get(f'habitacion_{habitacion_index}_ninos', '0') or 0)
        cant_adultos = int(request.POST.get(f'habitacion_{habitacion_index}_cant_adultos', '0') or 0)
        cant_ninos = int(request.POST.get(f'habitacion_{habitacion_index}_cant_ninos', '0') or 0)
        fechas_viaje = request.POST.get(f'habitacion_{habitacion_index}_fechas_viaje', '')

        habitaciones.append({
            'habitacion': nombre_habitacion,
            'adultos': num_adultos,
            'ninos': num_ninos,
            'precio': opcion_seleccionada['precio'],
            'cant_adultos': cant_adultos,
            'cant_ninos': cant_ninos,
            'fechas_viaje': fechas_viaje,
            'opcion': opcion_seleccionada['opcion'],
            'adultos_numeros': list(range(1, num_adultos + 1)),
            'ninos_numeros': list(range(1, num_ninos + 1)),
        })

    # Preparar el contexto para la plantilla
    context = {
        'precio_total': precio_total,
        'hotel': hotel,
        'habitaciones': habitaciones,
        # Usar los datos GET capturados previamente
        'destino': destino,
        'fechas_viaje': fechas_viaje,
        'adultos': adultos,
        'ninos': ninos,
        'info_habitaciones': info_habitaciones_decoded,
        'opciones_seleccionadas': opciones_seleccionadas,
    }
    
    return render(request, 'booking/hotel/hotel_pago_reserva.html', context)

# Función para enviar un correo de confirmación de la reserva
def correo_confirmacion(reserva): 
    hotel = reserva.hotel
    proveedor = hotel.proveedor

    # Filtrar los pasajeros relacionados con la reserva
    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
    
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
    
    agencia = {
        "nombre": "Viajes Felices S.A.",
        "direccion": "Calle Principal 123, Ciudad Turística",
        "usuario": "agente001",
        "email": "agente001@viajesfelices.com"
    }
    
    encabezado = "Muchas gracias por reservar con RUTA MULTISERVICE, estamos procesando su solicitud:"

    # Preparar el contenido del correo
    contenido = f"""
    Reserva para el hotel: {hotel.hotel_nombre}
    Fechas de viaje: {habitaciones[0].fechas_viaje if habitaciones else 'No especificadas'}
    Número de habitaciones: {habitaciones.count()}
    Número total de pasajeros: {pasajeros.count()}
    Precio total: ${reserva.precio_total}
    
    Detalles de las habitaciones:
    """
    
    # Agregar detalles de las habitaciones al correo
    for habitacion in habitaciones:
        contenido += f"""
        Habitación: {habitacion.habitacion_nombre}
        Adultos: {habitacion.adultos}
        Niños: {habitacion.ninos}
        Precio: ${habitacion.precio}
        """
    
    # Agregar detalles de los pasajeros al correo
    contenido += "\nDetalles de los pasajeros:\n"
    for pasajero in pasajeros:
        contenido += f"""
        Nombre: {pasajero.nombre}
        Tipo: {'Adulto' if pasajero.tipo == 'adulto' else 'Niño'}
        Pasaporte: {pasajero.pasaporte}
        """

    # Enviar el correo de confirmación
    # Elimina 'contenido' y 'proveedor.correo1' de la llamada
    enviar_correo(reserva, pasajeros, habitaciones, reserva.email_empleado, encabezado)

# Vista para completar la solicitud de reserva
@transaction.atomic
def complete_solicitud(request, hotel_id):
    destinos = PoloTuristico.objects.all()
    context = {'destinos': destinos}

    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        post_data = request.POST
        nombre_usuario = f"{request.user.agencia}"
        email_empleado = post_data.get('email_empleado', '')
        notas = post_data.get('notas', '')
        fechas_viaje = post_data.get('habitacion_fechas_viaje', '')
        precio_total = post_data.get('precio_total', '')

        # Validar y procesar fechas de viaje
        try:
            fecha_inicio_str, fecha_fin_str = fechas_viaje.split(' - ')
            fecha_inicio = datetime.strptime(fecha_inicio_str.strip(), '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin_str.strip(), '%Y-%m-%d')
            cantidad_noches = (fecha_fin - fecha_inicio).days
        except ValueError:
            messages.error(request, "Las fechas de viaje no son válidas.")
            return redirect('hotel_detalle', hotel_id=hotel_id)

        # Obtener el número de habitaciones
        try:
            habitacion_count = int(post_data.get('habitacion_count', 0))
        except ValueError:
            messages.error(request, "La cantidad de habitaciones no es válida.")
            return redirect('hotel_detalle', hotel_id=hotel_id)

        personas_por_habitacion = []

        # Obtener las ofertas disponibles para el hotel
        ofertas = Oferta.objects.filter(hotel=hotel, disponible=True)

        # Iterar sobre cada habitación para procesar y recalcular los precios
        for habitacion_index in range(1, habitacion_count + 1):
            habitacion_info = {
                'adultos': [],
                'ninos': [],
                'precio': Decimal('0.00'),
                'precio_sin_fee': Decimal('0.00'),
                'total_fee': Decimal('0.00'),
                'opcion': {}
            }

            # Obtener el nombre de la opción seleccionada desde el formulario POST
            habitacion_nombre = post_data.get(f"habitacion_{habitacion_index}_nombre", f"Habitación {habitacion_index}")
            habitacion_info['opcion']['nombre'] = habitacion_nombre

            # Obtener el número de adultos y niños
            try:
                num_adultos = int(post_data.get(f"habitacion_{habitacion_index}_adultos", 0))
                num_ninos = int(post_data.get(f"habitacion_{habitacion_index}_ninos", 0))
            except ValueError:
                messages.error(request, "El número de adultos o niños no es válido.")
                return redirect('hotel_detalle', hotel_id=hotel_id)

            # Procesar adultos
            for i in range(1, num_adultos + 1):
                nombre = post_data.get(f"nombre{habitacion_index}_adulto{i}")
                fecha_nacimiento = post_data.get(f"fecha_nacimiento{habitacion_index}_adulto{i}")
                pasaporte = post_data.get(f"pasaporte{habitacion_index}_adulto{i}")
                caducidad = post_data.get(f"caducidad{habitacion_index}_adulto{i}")
                pais_emision = post_data.get(f"pais_emision{habitacion_index}_adulto{i}")
                email = post_data.get(f"email{habitacion_index}_adulto{i}")
                telefono = post_data.get(f"telefono{habitacion_index}_adulto{i}")

                habitacion_info['adultos'].append({
                    'nombre': nombre,
                    'fecha_nacimiento': fecha_nacimiento,
                    'pasaporte': pasaporte,
                    'caducidad': caducidad,
                    'pais_emision': pais_emision,
                    'email': email,
                    'telefono': telefono,
                })

            # Procesar niños
            edades_ninos = []
            for i in range(1, num_ninos + 1):
                nombre = post_data.get(f"nombre{habitacion_index}_nino{i}")
                fecha_nacimiento = post_data.get(f"fecha_nacimiento{habitacion_index}_nino{i}")
                pasaporte = post_data.get(f"pasaporte{habitacion_index}_nino{i}")
                caducidad = post_data.get(f"caducidad{habitacion_index}_nino{i}")
                pais_emision = post_data.get(f"pais_emision{habitacion_index}_nino{i}")
                edad = post_data.get(f"edad_nino{habitacion_index}_{i}", '0')
                try:
                    edades_ninos.append(int(edad))
                except ValueError:
                    edades_ninos.append(0)

                habitacion_info['ninos'].append({
                    'nombre': nombre,
                    'fecha_nacimiento': fecha_nacimiento,
                    'pasaporte': pasaporte,
                    'caducidad': caducidad,
                    'pais_emision': pais_emision
                })

            # Recalcular el precio en el servidor
            cant_adultos = num_adultos
            cant_ninos = num_ninos
            nino1 = 1 if cant_ninos >= 1 else 0
            nino2 = 1 if cant_ninos >= 2 else 0

            # Obtener la habitación correspondiente
            try:
                habitacion_obj = Habitacion.objects.get(hotel=hotel, tipo=habitacion_nombre)
            except Habitacion.DoesNotExist:
                messages.error(request, f"No se encontró la habitación {habitacion_nombre} en el hotel.")
                return redirect('hotel_detalle', hotel_id=hotel_id)

            # Recalcular el precio usando las funciones existentes
            try:
                precio_total_habitacion, precio_sin_fee_habitacion, total_fee_habitacion = calcular_precios_por_tipo_habitacion(
                    cant_adultos, nino1, nino2, fechas_viaje, ofertas, habitacion_obj
                )

                # Convertir a Decimal para cálculos precisos
                habitacion_info['precio'] = Decimal(str(precio_total_habitacion))
                habitacion_info['precio_sin_fee'] = Decimal(str(precio_sin_fee_habitacion))
                habitacion_info['total_fee'] = Decimal(str(total_fee_habitacion))
            except Exception as e:
                messages.error(request, f"Error al calcular el precio de la habitación: {e}")
                return redirect('hotel_detalle', hotel_id=hotel_id)

            personas_por_habitacion.append(habitacion_info)

        # Calcular el precio total, costo sin fee y total de fees              
        costo_sin_fee = sum(habitacion['precio_sin_fee'] for habitacion in personas_por_habitacion)
        total_fees = sum(habitacion['total_fee'] for habitacion in personas_por_habitacion)

        # Calcular el costo total (para el agente) sumando el costo sin fee y los fees 
        costo_total = total_fees
        
        #Convertir el Precio total de STR a Decimal 
        precio_total_str = precio_total.replace(',', '.') 
        precio_total = Decimal(precio_total_str)

        # Redondear a dos decimales si es necesario
        precio_total = precio_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo_sin_fee = costo_sin_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo_total = costo_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Crear la reserva
        reserva = Reserva.objects.create(
            hotel=hotel,
            fecha_reserva=timezone.now(),
            nombre_usuario=nombre_usuario,
            email_empleado=email_empleado,
            notas=notas,
            costo_total=costo_total,  # Ahora asignamos el costo total correcto
            costo_sin_fee=costo_sin_fee,
            precio_total=precio_total,
            tipo='hoteles',
            estatus='solicitada'
        )

        habitaciones = []

        # Crear las habitaciones y pasajeros asociados
        for habitacion_index, habitacion_info in enumerate(personas_por_habitacion, start=1):
            habitacion_reserva = HabitacionReserva.objects.create(
                reserva=reserva,
                habitacion_nombre=habitacion_info['opcion']['nombre'],
                adultos=len(habitacion_info['adultos']),
                ninos=len(habitacion_info['ninos']),
                fechas_viaje=fechas_viaje,
                precio=habitacion_info['precio'],
                oferta_codigo=post_data.get(f"oferta_codigo_{habitacion_index}", '')
            )

            habitaciones.append(habitacion_reserva)

            for adulto in habitacion_info['adultos']:
                try:
                    pasajero = Pasajero.objects.create(
                        habitacion=habitacion_reserva,
                        nombre=adulto['nombre'],
                        fecha_nacimiento=datetime.strptime(adulto['fecha_nacimiento'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pasaporte=adulto['pasaporte'],
                        caducidad_pasaporte=datetime.strptime(adulto['caducidad'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pais_emision_pasaporte=adulto['pais_emision'],
                        email=adulto['email'],
                        telefono=adulto['telefono'],
                        tipo='adulto'
                    )
                except ValueError:
                    messages.error(request, "Las fechas de nacimiento o caducidad no son válidas.")
                    return redirect('hotel_detalle', hotel_id=hotel_id)

            for nino in habitacion_info['ninos']:
                try:
                    pasajero = Pasajero.objects.create(
                        habitacion=habitacion_reserva,
                        nombre=nino['nombre'],
                        fecha_nacimiento=datetime.strptime(nino['fecha_nacimiento'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pasaporte=nino['pasaporte'],
                        caducidad_pasaporte=datetime.strptime(nino['caducidad'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pais_emision_pasaporte=nino['pais_emision'],
                        email='',
                        telefono='',
                        tipo='nino'
                    )
                except ValueError:
                    messages.error(request, "Las fechas de nacimiento o caducidad no son válidas.")
                    return redirect('hotel_detalle', hotel_id=hotel_id)

        reserva.save()

        # Enviar correo de confirmación
        correo_confirmacion(reserva)

        messages.success(request, 'Reserva completada con éxito.')
        return redirect('booking:user_dashboard')

    return redirect('booking:user_dashboard')

# ================================================================================================== #
# -------------------------------- Sección: Reservas Hoteles --------------------------------------- #
# ================================================================================================== #

@login_required
def listar_reservas(request, estado=None):
    usuario = request.user  # Obtiene el usuario autenticado

    # Filtrar todas las reservas del usuario por su nombre
    reservas = Reserva.objects.filter(nombre_usuario__iexact=usuario.agencia).order_by('fecha_reserva')

    # Obtener estado desde GET si no se ha proporcionado como argumento
    if not estado:
        estado = request.GET.get('estado', None)
    
    # Filtrar por estado
    if estado:
        if estado == 'por_cobrar':
            reservas = reservas.filter(cobrada=False)
        elif estado == 'pagada':
            reservas = reservas.filter(pagada=True)
        else:
            reservas = reservas.filter(estatus__iexact=estado)  # Asegura la coincidencia con diferentes formatos de estado

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
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            reservas = reservas.filter(fecha_reserva__gte=fecha_inicio)
        except ValueError:
            pass  # Maneja errores en el formato de fecha si es necesario

    if fecha_fin:
        try:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            reservas = reservas.filter(fecha_reserva__lte=fecha_fin)
        except ValueError:
            pass  # Maneja errores en el formato de fecha si es necesario

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
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else '',
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d') if fecha_fin else '',
    }
    return render(request, 'booking/reservas/listar_reservas.html', context)

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
        #print("Reserva no encontrada con ID:", reserva_id)
        return JsonResponse({'error': 'Reserva no encontrada.'}, status=404)

    except Exception as e:
        # Captura otros errores y los muestra en la consola del servidor
        print(f"Error al obtener los detalles de la reserva: {e}")
        return JsonResponse({'error': 'Error al cargar los detalles de la reserva.'}, status=500)

# ================================================================================================== #
# ---------------------------------------- Sección: Remesas ---------------------------------------- #
# ================================================================================================== #

@login_required
def remesas(request):
    usuario = request.user  # Obtiene el usuario autenticado
    
    # Obtener la tasa de cambio más reciente
    try:
        tasa_cambio = TasaCambio.objects.latest('fecha_actualizacion')
    except TasaCambio.DoesNotExist:
        tasa_cambio = None  # Si no hay tasa de cambio, se manejará en la plantilla

    context = {
        'tasa_cambio': tasa_cambio,
        'usuario': usuario
    }

    return render(request, 'booking/remesas/remesas.html', context)

@login_required
def guardar_remesa(request):
    if request.method == 'POST':
        # Captura de los datos del formulario
        nombre_remitente = request.POST.get('nombreRemitente')
        documento_remitente = request.POST.get('documentoRemitente')
        telefono_remitente = request.POST.get('telefonoRemitente')
        email_remitente = request.POST.get('emailRemitente', '')

        nombre_destinatario = request.POST.get('nombreDestinatario')
        telefono_destinatario = request.POST.get('telefonoDestinatario')
        direccion_destinatario = request.POST.get('direccionDestinatario')

        monto_envio = request.POST.get('montoEnvio')
        moneda_envio = request.POST.get('monedaEnvio')
        moneda_recepcion = request.POST.get('monedaRecepcion')

        # Validación básica
        if not (nombre_remitente and documento_remitente and telefono_remitente and nombre_destinatario and telefono_destinatario and direccion_destinatario):
            messages.error(request, 'Por favor, complete todos los campos obligatorios.')
            return redirect('remesas')

        try:
            # Obtener la tasa de cambio más reciente
            tasa_cambio = TasaCambio.objects.latest('fecha_actualizacion')
            if moneda_envio == 'USD' and moneda_recepcion == 'CUP':
                tasa = tasa_cambio.tasa_cup
            elif moneda_envio == 'USD' and moneda_recepcion == 'MLC':
                tasa = tasa_cambio.tasa_mlc
            elif moneda_envio == 'CUP' and moneda_recepcion == 'USD':
                tasa = 1 / tasa_cambio.tasa_cup
            elif moneda_envio == 'MLC' and moneda_recepcion == 'USD':
                tasa = 1 / tasa_cambio.tasa_mlc
            else:
                tasa = 1.0  # Por defecto, USD -> USD

            # Convertimos monto_envio a Decimal para evitar errores al multiplicar con tasa
            monto_estimado_recepcion = Decimal(monto_envio) * tasa

            # Guardar la Remesa
            remesa = Remesa.objects.create(
                nombre_remitente=nombre_remitente,
                documento_remitente=documento_remitente,
                telefono_remitente=telefono_remitente,
                email_remitente=email_remitente,
                nombre_destinatario=nombre_destinatario,
                telefono_destinatario=telefono_destinatario,
                direccion_destinatario=direccion_destinatario,
                monto_envio=monto_envio,
                moneda_envio=moneda_envio,
                monto_estimado_recepcion=monto_estimado_recepcion,
                moneda_recepcion=moneda_recepcion
            )

            # Guardar la Reserva vinculada a la remesa
            reserva = Reserva.objects.create(
                remesa=remesa,  # Relación con la remesa
                nombre_usuario=request.user.agencia,
                email_empleado=request.user.email,
                costo_total=monto_envio,
                precio_total=monto_estimado_recepcion,
                tipo='remesas',
                estatus='solicitada',
                numero_confirmacion=None,  # Puedes generar un número de confirmación si es necesario
                cobrada=False,
                pagada=False,
                fecha_reserva=datetime.now()
            )

            messages.success(request, f'Remesa enviada con éxito. Reserva #{reserva.id}')
            return redirect('remesas')  # Redirige a la vista de remesas o a donde desees

        except Exception as e:
            messages.error(request, f'Error al procesar la remesa: {str(e)}')
            return redirect('booking:remesas')

    else:
        return redirect('booking:remesas')


# ================================================================================================== #
# -------------------------------- Sección: Reservas Hoteles --------------------------------------- #
# ================================================================================================== #

@login_required
def traslados_search(request):
    ubicaciones = Ubicacion.objects.all()  # Obtener todos las ubicaciopnes turísticos
    context = {
        'ubicaciones': ubicaciones,
    } 
    return render(request, 'booking/traslados_search.html', context)

@login_required
def traslado_dashboard(request):
    ubicaciones = Ubicacion.objects.all()  # Obtener todos las ubicaciopnes turísticos
    context = {
        'ubicaciones': ubicaciones,
    }    
    return render(request, 'booking/traslados/dashboard.html', context)




def obtener_destinos(request):
    """ Devuelve los destinos disponibles según el origen seleccionado sin duplicados """
    origen_id = request.GET.get('origen_id')

    if origen_id:
        traslados = (
            Traslado.objects
            .filter(origen_id=origen_id)
            .values(nombre=F('destino__nombre'))
            .distinct()
        )
        destinos = [{'nombre': traslado['nombre']} for traslado in traslados]
    else:
        destinos = []

    return JsonResponse({'destinos': destinos})





# ================================================================================================== #
# -------------------------------- Sección: Por Desarrollar ---------------------------------------- #
# ================================================================================================== #

# Vista placeholder para la búsqueda de alquiler de coches
@login_required
def car_rental_search(request):
    return render(request, 'booking/car_rental_search.html')

# Vista placeholder para la búsqueda de transferencias
@login_required
def transfers_search(request):
    lugares = PoloTuristico.objects.all()  # Obtener todos los lugares turísticos
    return render(request, 'booking/transfers_search.html', {'lugares': lugares})

