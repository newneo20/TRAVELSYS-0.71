# finanzas/views.py 

from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import ( 
    Q, Sum, Case, When, F, FloatField, DecimalField
)
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from backoffice.models import Reserva
from usuarios.models import CustomUser
from .forms import TransaccionForm
from .models import Transaccion




def listar_reservas_finanzas(request, estado=None):
    reservas = Reserva.objects.all().order_by('fecha_reserva')

    # Filtrar por estado si se especifica
    if estado:
        reservas = reservas.filter(estatus=estado)

    # Filtrar por ID de Reserva
    id_reserva = request.GET.get('id_reserva', '')
    if id_reserva:
        reservas = reservas.filter(id=id_reserva)

    # Filtrar por búsqueda general (Hotel, Usuario, Email)
    query = request.GET.get('q', '')
    if query:
        reservas = reservas.filter(
            Q(nombre_usuario__icontains=query) |
            Q(email_empleado__icontains=query) |            
            Q(hotel__hotel_nombre__icontains=query)  # Asegúrate de que este campo existe
        )

    # Filtrar por Nombre del Pasajero
    nombre_pasajero = request.GET.get('nombre_pasajero', '')
    if nombre_pasajero:
        reservas = reservas.filter(
            habitaciones_reserva__pasajeros__nombre__icontains=nombre_pasajero
        ).distinct()

    # Filtrar por rango de fechas
    fecha_inicio = request.GET.get('fecha_inicio', None)
    fecha_fin = request.GET.get('fecha_fin', None)
    if fecha_inicio:
        reservas = reservas.filter(fecha_reserva__gte=fecha_inicio)
    if fecha_fin:
        reservas = reservas.filter(fecha_reserva__lte=fecha_fin)

    # Paginación
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reservas': page_obj,
        'query': query,
        'id_reserva': id_reserva,
        'nombre_pasajero': nombre_pasajero,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado': estado,
    }
    return render(request, 'finanzas/listar_reservas_finanzas.html', context)


@transaction.atomic
def transacciones_view(request, reserva_id):
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)

    # Obtener las transacciones asociadas
    transacciones = Transaccion.objects.filter(reserva=reserva).order_by('-fecha')

    # Calcular los saldos actuales
    monto_cobrado = sum(trans.monto for trans in transacciones if trans.tipo == 'cobro')
    monto_pagado = sum(trans.monto for trans in transacciones if trans.tipo == 'pago')
    monto_reembolsado = sum(trans.monto for trans in transacciones if trans.tipo == 'reembolso')

    saldo_por_cobrar = reserva.costo_total - monto_cobrado + monto_reembolsado
    saldo_por_pagar = reserva.costo_sin_fee - monto_pagado

    ganancia = reserva.costo_total - reserva.costo_sin_fee

    # Verificar si la reserva debe marcarse como cobrada o pagada
    if saldo_por_cobrar <= Decimal('0.00') and not reserva.cobrada:
        reserva.cobrada = True
        reserva.save()

    if saldo_por_pagar <= Decimal('0.00') and not reserva.pagada:
        reserva.pagada = True
        reserva.save()

    # Si la reserva ya está cobrada/pagada, ajustar el saldo pendiente del usuario
    usuario = reserva.nombre_usuario  # Ajusta esto según cómo se relacione el usuario con la reserva
    if saldo_por_cobrar < Decimal('0.00') or saldo_por_pagar < Decimal('0.00'):
        exceso_cobro = abs(saldo_por_cobrar) if saldo_por_cobrar < Decimal('0.00') else Decimal('0.00')
        exceso_pago = abs(saldo_por_pagar) if saldo_por_pagar < Decimal('0.00') else Decimal('0.00')

        username = reserva.nombre_usuario  # Asegúrate de que 'nombre_usuario' es el 'username' del usuario
        usuario = get_object_or_404(CustomUser, agencia=username)
        usuario.save()

    # Procesar formulario de nueva transacción
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            nueva_transaccion = form.save(commit=False)
            nueva_transaccion.reserva = reserva

            # Verificar tipo de acción
            action = request.POST.get('action')
            if action == 'add':
                nueva_transaccion.save()
                messages.success(request, "Transacción agregada con éxito.")
            elif action == 'refund':
                # Realizar un reembolso total
                monto_reembolso = monto_cobrado  # El monto reembolsado es el total cobrado
                nueva_transaccion.monto = monto_reembolso
                nueva_transaccion.tipo = 'reembolso'
                nueva_transaccion.save()

                # Ajustar saldo del usuario
                usuario.saldo_pendiente -= monto_reembolso
                usuario.save()

                messages.success(request, "Reembolso realizado con éxito.")

            return redirect('transacciones', reserva_id=reserva.id)
    else:
        form = TransaccionForm()

    context = {
        'reserva': reserva,
        'transacciones': transacciones,
        'form': form,
        'saldo_por_cobrar': saldo_por_cobrar,
        'saldo_por_pagar': saldo_por_pagar,
        'ganancia': ganancia,
    }

    return render(request, 'finanzas/transacciones.html', context)

@require_POST
def transaccion_eliminar(request, reserva_id, transaccion_id):
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Obtener la transacción y asegurarse de que pertenece a la reserva
    transaccion = get_object_or_404(Transaccion, id=transaccion_id, reserva=reserva)
    
    # Eliminar la transacción
    transaccion.delete()
    messages.success(request, "Transacción eliminada con éxito.")
    
    # Redirigir a la página de transacciones de la reserva
    return redirect('transacciones', reserva_id=reserva.id)
