# usuarios/views.py
from django.contrib import messages # type: ignore
from django.http import JsonResponse # type: ignore
from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth import logout, login, authenticate # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from backoffice import models
from backoffice.funciones_externas import combinacion_habitaciones, leer_datos_hoteles, generar_voucher_pdf, enviar_correo, calcular_precio_total_por_mes, contar_reservas_por_mes
from usuarios.decorators import manager_required
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from django.core.paginator import Paginator # type: ignore
from django.contrib.auth.forms import AuthenticationForm # type: ignore
from backoffice.models import Hotel, PlanAlimenticio, Proveedor, PoloTuristico, Habitacion, TipoFee, Oferta,HotelFacility,HotelSetting, CadenaHotelera, Reserva, Pasajero
from django.utils import timezone # type: ignore
from datetime import datetime, timedelta, date
from django.db.models import Sum, Q # type: ignore
from django.db.models import Avg # type: ignore
from django.db.models import Count # type: ignore
from collections import defaultdict
from decimal import Decimal
from collections import Counter



@login_required
def check_session_status(request):
    # Si el usuario está autenticado, devuelve "active", de lo contrario "inactive"
    return JsonResponse({'status': 'active'})

@login_required
def home(request):
    # Forzar cierre de sesión al iniciar el servidor (solo para desarrollo)
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'usuarios/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_manager:
                return redirect('dashboard')
            else:
                return redirect('booking:user_dashboard')
        else:
            # Add an error message if authentication fails
            messages.error(request, 'Error de Usuario y contraseña.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

@login_required
def index(request):
    return render(request, 'renta_hoteles/index.html')

def logout_view(request):
    logout(request)    
    return redirect('login')


@login_required
def reservar_hotel(request):
    return render(request, 'renta_hoteles/reservar_hotel.html')


@login_required
@manager_required
def dashboard(request):
    # Obtener el rango seleccionado desde la solicitud GET
    rango = request.GET.get('range', 'mes')

    # Definir las fechas iniciales y finales basadas en el rango seleccionado
    hoy = timezone.now().date()
    
    if rango == 'hoy':
        fecha_inicio = hoy
        selected_range = 'Hoy'
    elif rango == '7_dias':
        fecha_inicio = hoy - timedelta(days=7)
        selected_range = 'Últimos 7 días'
    elif rango == '30_dias':
        fecha_inicio = hoy - timedelta(days=30)
        selected_range = 'Últimos 30 días'
    elif rango == 'mes':
        fecha_inicio = hoy.replace(day=1)
        selected_range = 'Este mes'
    elif rango == 'ano':
        fecha_inicio = hoy.replace(month=1, day=1)
        selected_range = 'Este año'
    else:
        fecha_inicio = hoy.replace(day=1)
        selected_range = 'Este mes'

    # Filtrar las reservas según la fecha
    reservas = Reserva.objects.filter(fecha_reserva__gte=fecha_inicio)
    
    hoteles = Hotel.objects.all()
    usuarios = CustomUser.objects.all()
    ultimos_usuarios = CustomUser.objects.order_by('-date_joined')[:5]


    # Los Ingresos Totales y Gastos Totales
    ingresos_totales = reservas.filter(cobrada=True, pagada=True).aggregate(total_ingresos=Sum('precio_total'))['total_ingresos'] or 0.0
    gastos_totales = reservas.filter(cobrada=True, pagada=True).aggregate(total_gastos=Sum('costo_total'))['total_gastos'] or 0.0
        
    ingresos_totales = float(ingresos_totales)
    gastos_totales = float(gastos_totales)
    
    reservas_activas = [reserva for reserva in reservas if reserva.esta_activa()]

    # Generar datos para los gráficos
    labels_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    datos_reservas_mensuales = contar_reservas_por_mes(reservas)
    datos_ingresos = [float(calcular_ingresos_mes(mes, reservas)) for mes in range(1, 13)]
    datos_gastos = [float(calcular_gastos_mes(mes, reservas)) for mes in range(1, 13)]
    
    # Genera dos listas con las Reservas que tienen ALERTAS de cobro y de pago 
    reservas_alerta_pago, reservas_alerta_cobro = obtener_reservas_alerta(Reserva.objects.all())
    
    # Calcula el  tiempo Promedio de Reservas
    tiempo_promedio_reserva = calcular_tiempo_promedio_reserva()
    
    # Crea un top 5 de las agencoias que mas venden
    top_agencias = top_5_agencias_mas_reservas()
    
    # Crea un top 5 de los hoteles mas vendidos
    top_hoteles = top_5_hoteles_mas_reservados()
    
        
    context = {
        'hoteles': hoteles,
        'reservas': reservas,
        'usuarios': usuarios,
        'ingresos_totales': ingresos_totales,
        'gastos_totales': gastos_totales,
        'reservas_activas': reservas_activas, 
        'labels_meses': labels_meses,
        'datos_reservas_mensuales': datos_reservas_mensuales,
        'datos_ingresos': datos_ingresos,
        'datos_gastos': datos_gastos,
        'reservas_alerta_pago': reservas_alerta_pago,
        'reservas_alerta_cobro': reservas_alerta_cobro,
        'selected_range': selected_range,  # Pasar el rango seleccionado al contexto
        'tiempo_promedio_reserva': tiempo_promedio_reserva,
        'top_agencias': top_agencias,
        'top_hoteles': top_hoteles,
        'ultimos_usuarios': ultimos_usuarios,

    }
    return render(request, 'usuarios/dashboard.html', context)

def calcular_ingresos_mes(mes, reservas):
    total = reservas.filter(fecha_reserva__month=mes, cobrada=True, pagada=True).aggregate(total=Sum('precio_total'))['total'] or 0.0
    return float(total)

def calcular_gastos_mes(mes, reservas):
    total = reservas.filter(fecha_reserva__month=mes, cobrada=True, pagada=True).aggregate(total=Sum('costo_total'))['total'] or 0.0
    return float(total)

def contar_reservas_por_mes(reservas):
    return [reservas.filter(fecha_reserva__month=mes).count() for mes in range(1, 13)]

def obtener_reservas_alerta(reservas):
    hoy = timezone.now().date()  # Fecha actual
    quince_dias_despues = hoy + timedelta(days=15)
    
    reservas_alerta_pago = []
    reservas_alerta_cobro = []
    
    for reserva in reservas:
        if reserva.tipo == 'hoteles':  # Filtrar por tipo de reserva
            for habitacion in reserva.habitaciones_reserva.all():
                # Separar las fechas de check-in y check-out
                fechas = habitacion.fechas_viaje.split(' - ')
                check_in = datetime.strptime(fechas[0], '%Y-%m-%d').date()
                check_out = datetime.strptime(fechas[1], '%Y-%m-%d').date()

                # Comparar la fecha actual con el check-in
                if hoy <= check_in <= quince_dias_despues:
                    if not reserva.pagada:
                        reservas_alerta_pago.append(reserva)
                    if not reserva.cobrada:
                        reservas_alerta_cobro.append(reserva)

    return reservas_alerta_pago, reservas_alerta_cobro

def calcular_tiempo_promedio_reserva():
    reservas = Reserva.objects.all()  # Obtiene todas las reservas

    # Lista para almacenar los tiempos (en días) entre la fecha de reserva y el check-in
    tiempos_reserva = []

    for reserva in reservas:
        # Para cada reserva, obtenemos las habitaciones relacionadas
        for habitacion in reserva.habitaciones_reserva.all():
            # Extraemos las fechas de check-in y check-out
            fechas = habitacion.fechas_viaje.split(' - ')
            check_in_str = fechas[0]  # El check-in es la primera parte del rango
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()

            # Calculamos la diferencia en días entre la fecha de la reserva y el check-in
            diferencia_dias = (check_in - reserva.fecha_reserva.date()).days
            tiempos_reserva.append(diferencia_dias)

    # Calculamos el promedio de días
    if tiempos_reserva:
        tiempo_promedio_reserva = sum(tiempos_reserva) / len(tiempos_reserva)
    else:
        tiempo_promedio_reserva = 0  # Si no hay reservas, el promedio es 0

    return tiempo_promedio_reserva

def top_5_agencias_mas_reservas():
    reservas = Reserva.objects.all()
    conteo_reservas = defaultdict(lambda: {'total_reservas': 0, 'ingresos': Decimal('0.00')})

    for reserva in reservas:
        if reserva.nombre_usuario:
            conteo_reservas[reserva.nombre_usuario]['total_reservas'] += 1
            conteo_reservas[reserva.nombre_usuario]['ingresos'] += reserva.precio_total

    total_reservas = sum(data['total_reservas'] for data in conteo_reservas.values())

    lista_agencias = sorted(
        [
            {
                'agencia': agencia,
                'total_reservas': data['total_reservas'],
                'ingresos': data['ingresos'],
                'porcentaje': round((data['total_reservas'] / total_reservas * 100), 1) if total_reservas > 0 else 0
            }
            for agencia, data in conteo_reservas.items()
        ],
        key=lambda x: x['total_reservas'],
        reverse=True
    )

    return lista_agencias[:5]

def top_5_hoteles_mas_reservados():
    """
    Obtiene el top 5 de hoteles con más reservas.
    """
    # Filtrar solo reservas asociadas a hoteles
    reservas_hoteles = Reserva.objects.filter(hotel__isnull=False)

    # Contar las reservas por hotel
    from collections import Counter
    conteo_reservas = Counter(reserva.hotel for reserva in reservas_hoteles)

    # Formatear los datos en una lista de diccionarios, ordenados por número de reservas descendente
    top_hoteles = [
        {
            'hotel_nombre': hotel.hotel_nombre,
            'num_reservas': total_reservas,
            'ingresos_totales': reservas_hoteles.filter(hotel=hotel).aggregate(
                ingresos_totales=Sum('precio_total')
            )['ingresos_totales'] or 0,
        }
        for hotel, total_reservas in conteo_reservas.most_common(5)
    ]

    return top_hoteles




@manager_required
@login_required
def listar_usuarios(request):
    query = request.GET.get('q')
    usuarios_list = CustomUser.objects.all()
    if query:
        usuarios_list = usuarios_list.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(direccion__icontains=query)
        )
    paginator = Paginator(usuarios_list, 10)  # Mostrar 10 usuarios por página
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios, 'query': query})

@manager_required
@login_required
def crear_usuario(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        agencia = request.POST.get('agencia')
        username = request.POST.get('username')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        nombre_dueno = request.POST.get('nombre_dueno')
        telefono_dueno = request.POST.get('telefono_dueno')
        is_manager = request.POST.get('is_manager') == 'on'
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')  # Asegúrate de tener este campo en el formulario
        fee_hotel = request.POST.get('fee_hotel')
        tipo_fee_hotel = request.POST.get('tipo_fee_hotel')
        fee_carro = request.POST.get('fee_carro')
        tipo_fee_carro = request.POST.get('tipo_fee_carro')
        fee_tarara = request.POST.get('fee_tarara')
        tipo_fee_tarara = request.POST.get('tipo_fee_tarara')
        logo = request.FILES.get('logo')  # Manejar archivo subido
        print('antes de salvar:')
        print(agencia)
        # Validar que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'usuarios/crear_usuario.html')
        
        # Crear un nuevo usuario con la contraseña correctamente encriptada
        nuevo_usuario = CustomUser(
            agencia=agencia,
            username=username,
            email=email,
            telefono=telefono,
            direccion=direccion,
            nombre_dueno=nombre_dueno,
            telefono_dueno=telefono_dueno,
            is_manager=is_manager,
            fee_hotel=fee_hotel,
            tipo_fee_hotel=tipo_fee_hotel,
            fee_carro=fee_carro,
            tipo_fee_carro=tipo_fee_carro,
            fee_tarara=fee_tarara,
            tipo_fee_tarara=tipo_fee_tarara,
            logo=logo,
        )
        nuevo_usuario.set_password(password)  # Encriptar la contraseña
        nuevo_usuario.save()
        print('despues de salvar:')
        print(nuevo_usuario.agencia)
        # Mensaje de éxito y redirección
        messages.success(request, "Usuario creado exitosamente.")
        return redirect('listar_usuarios')

    return render(request, 'usuarios/crear_usuario.html')

@manager_required
@login_required
# usuarios/views.py
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(CustomUser, id=usuario_id)
    
    if request.method == 'POST':
        # Capturar los datos del formulario        
        usuario.agencia = request.POST.get('agencia')
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        usuario.telefono = request.POST.get('telefono')
        usuario.direccion = request.POST.get('direccion')
        usuario.nombre_dueno = request.POST.get('nombre_dueno')
        usuario.telefono_dueno = request.POST.get('telefono_dueno')
        usuario.is_manager = request.POST.get('is_manager') == 'on'
        password = request.POST.get('password')
        if password:  # Solo actualizar si se proporciona una nueva contraseña
            usuario.set_password(password)
        usuario.saldo_pendiente = request.POST.get('saldo_pendiente')
        usuario.fee_hotel = request.POST.get('fee_hotel')
        usuario.tipo_fee_hotel = request.POST.get('tipo_fee_hotel')
        usuario.fee_carro = request.POST.get('fee_carro')
        usuario.tipo_fee_carro = request.POST.get('tipo_fee_carro')
        usuario.fee_tarara = request.POST.get('fee_tarara')
        usuario.tipo_fee_tarara = request.POST.get('tipo_fee_tarara')
        if 'logo' in request.FILES:
            usuario.logo = request.FILES['logo']  # Manejar archivo subido
        
        usuario.save()
        return redirect('listar_usuarios')
    
    return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

@manager_required
@login_required
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('listar_usuarios')
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario': usuario})

