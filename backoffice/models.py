from django.core.exceptions import ValidationError # type: ignore
from django.db import models # type: ignore
from decimal import Decimal
from django.core.validators import MinValueValidator # type: ignore


# ==========================
# Modelos base y auxiliares
# ==========================
class Servicio(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    correo1 = models.EmailField(blank=True, null=True)
    correo2 = models.EmailField(blank=True, null=True)
    correo3 = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    detalles_cuenta_bancaria = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    # Relación ManyToMany para los servicios
    servicios = models.ManyToManyField(
        'Servicio',
        blank=True,
        related_name='proveedores',
        help_text="Seleccione los servicios ofrecidos por este proveedor."
    )

    def __str__(self):
        return self.nombre if self.nombre else "Proveedor sin nombre"

class TipoFee(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class PoloTuristico(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    pais = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class PlanAlimenticio(models.Model):
    siglas = models.CharField(max_length=255, blank=True, null=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class CadenaHotelera(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# ====================
# Modelos principales
# ====================
class Hotel(models.Model):
    hotel_nombre = models.CharField(max_length=255, blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    fee = models.CharField(max_length=10, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    tipo_fee = models.CharField(max_length=10, blank=True, null=True)
    polo_turistico = models.ForeignKey(PoloTuristico, on_delete=models.SET_NULL, null=True, blank=True)
    plan_alimenticio = models.CharField(max_length=10, blank=True, null=True)
    descripcion_hotel = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    checkin = models.CharField(max_length=10, blank=True, null=True)
    checkout = models.CharField(max_length=10, blank=True, null=True)    
    orden = models.IntegerField(blank=True, null=True)
    foto_hotel = models.CharField(max_length=255, blank=True, null=True)
    categoria = models.IntegerField(blank=True, null=True)
    cadena_hotelera = models.ForeignKey(CadenaHotelera, on_delete=models.SET_NULL, null=True, blank=True)
    solo_adultos = models.BooleanField(default=False)

    def __str__(self):
        return self.hotel_nombre or "Unnamed Hotel"

class Habitacion(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='habitaciones', blank=True, null=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    datetimes = models.CharField(max_length=255, blank=True, null=True)
    foto = models.ImageField(upload_to='habitacion_fotos/', blank=True, null=True)
    adultos = models.IntegerField(blank=True, null=True)
    ninos = models.IntegerField(blank=True, null=True)
    max_capacidad = models.IntegerField(blank=True, null=True)
    min_capacidad = models.IntegerField(blank=True, null=True)
    descripcion_capacidad = models.TextField(blank=True, null=True)
    admite_3_con_1 = models.BooleanField(default=False)
    solo_adultos = models.BooleanField(default=False)

    def __str__(self):
        return f"Habitación {self.tipo} en {self.hotel.hotel_nombre}"

    def clean(self):
        if self.adultos < 0 or self.ninos < 0:
            raise ValidationError("La cantidad de adultos o niños no puede ser negativa.")
        if self.max_capacidad and self.max_capacidad < self.min_capacidad:
            raise ValidationError("La capacidad máxima no puede ser menor que la mínima.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super(Habitacion, self).save(*args, **kwargs)

class ReservaHotel(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reservas', blank=True, null=True)
    noches = models.IntegerField(blank=True, null=True)
    fecha_reserva = models.DateField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Reserva en {self.hotel.hotel_nombre} para {self.noches} noches"

    def clean(self):
        if self.noches and self.noches <= 0:
            raise ValidationError("El número de noches debe ser positivo.")
        if self.total and self.total < 0:
            raise ValidationError("El total no puede ser negativo.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super(ReservaHotel, self).save(*args, **kwargs)

class Oferta(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    disponible = models.BooleanField(default=True)
    codigo = models.CharField(max_length=50)
    tipo_habitacion = models.CharField(max_length=50)
    temporada = models.CharField(max_length=50)
    booking_window = models.CharField(max_length=50, blank=True, null=True)
    sencilla = models.CharField(max_length=50, blank=True, null=True)
    doble = models.CharField(max_length=50, blank=True, null=True)
    triple = models.CharField(max_length=50, blank=True, null=True)
    primer_nino = models.CharField(max_length=50, blank=True, null=True)
    segundo_nino = models.CharField(max_length=50, blank=True, null=True)
    un_adulto_con_ninos = models.CharField(max_length=50, blank=True, null=True)
    primer_nino_con_un_adulto = models.CharField(max_length=50, blank=True, null=True)
    segundo_nino_con_un_adulto = models.CharField(max_length=50, blank=True, null=True)
    edad_nino = models.CharField(max_length=50, blank=True, null=True)
    edad_infante = models.CharField(max_length=50, blank=True, null=True)
    noches_minimas = models.CharField(max_length=50, blank=True, null=True)
    cantidad_habitaciones = models.IntegerField(default=1)    
    tipo_fee = models.CharField(max_length=10, blank=True, null=True)
    fee_doble = models.CharField(max_length=10, blank=True, null=True)
    fee_triple = models.CharField(max_length=10, blank=True, null=True)
    fee_sencilla = models.CharField(max_length=10, blank=True, null=True)
    fee_primer_nino = models.CharField(max_length=10, blank=True, null=True)
    fee_segundo_nino = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"Oferta {self.codigo} en {self.hotel.hotel_nombre}"

class HotelFacility(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    
    # Baño
    articulos_aseo = models.BooleanField(default=False)
    inodoro = models.BooleanField(default=False)
    toallas = models.BooleanField(default=False)
    bano_privado = models.BooleanField(default=False)
    banera_ducha = models.BooleanField(default=False)
    secador_pelo = models.BooleanField(default=False)
    
    # Seguridad
    extintores = models.BooleanField(default=False)
    detectores_humo = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    
    # Dormitorio
    ropa_cama = models.BooleanField(default=False)
    armario_ropero = models.BooleanField(default=False)
    
    # Comida y bebida
    bar = models.BooleanField(default=False)
    restaurante = models.BooleanField(default=False)
    menu_ninos = models.BooleanField(default=False)
    menu_dietetico = models.BooleanField(default=False)
    desayuno = models.BooleanField(default=False)
    tetera_cafetera = models.BooleanField(default=False)
    
    # General
    ascensor = models.BooleanField(default=False)
    discapacitados = models.BooleanField(default=False)
    hipoalergenico = models.BooleanField(default=False)
    habitaciones_familiares = models.BooleanField(default=False)
    prohibido_fumar = models.BooleanField(default=False)
    calefaccion = models.BooleanField(default=False)
    alfombrado = models.BooleanField(default=False)
    instalaciones_planchar = models.BooleanField(default=False)
    plancha = models.BooleanField(default=False)
    
    # Servicios de recepción
    guardaequipaje = models.BooleanField(default=False)
    factura_proporcionada = models.BooleanField(default=False)
    recepcion_24h = models.BooleanField(default=False)
    checkin_checkout_privado = models.BooleanField(default=False)
    
    # Medios y tecnología
    tv_pantalla_plana = models.BooleanField(default=False)
    radio = models.BooleanField(default=False)
    canales_via_satellite = models.BooleanField(default=False)
    tv = models.BooleanField(default=False)
    telefono = models.BooleanField(default=False)
    
    # Servicios de limpieza
    lavanderia = models.BooleanField(default=False)
    tintoreria = models.BooleanField(default=False)
    limpieza_diaria = models.BooleanField(default=False)
    
    def __str__(self):
        return self.hotel.hotel_nombre

class HotelSetting(models.Model):
    hotel = models.OneToOneField('Hotel', on_delete=models.CASCADE)
    edad_limite_nino = models.IntegerField(default=0)
    edad_limite_infante = models.IntegerField(default=0)
    cantidad_noches = models.IntegerField(default=0)

    def __str__(self):
        return f"Configuración del hotel {self.hotel.hotel_nombre}"

    def clean(self):
        if self.edad_limite_nino < 0:
            raise ValidationError('La edad límite del primer niño no puede ser negativa.')
        if self.edad_limite_infante < 0:
            raise ValidationError('La edad límite del infante no puede ser negativa.')
        if self.cantidad_noches < 0:
            raise ValidationError('La cantidad de noches no puede ser negativa.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(HotelSetting, self).save(*args, **kwargs)

class HabitacionOpcion(models.Model):
    habitacion = models.ForeignKey('Habitacion', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.nombre

class OfertasEspeciales(models.Model):
    codigo = models.CharField(max_length=10, blank=True, null=True) 
    disponible = models.BooleanField(default=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, blank=True, null=True, choices=[('hoteles', 'Hoteles'), 
                                                                           ('carros', 'Carros'), 
                                                                           ('vuelos', 'Vuelos'), 
                                                                           ('traslados', 'Traslados')])

class TasaCambio(models.Model):
    tasa_cup = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0)],  # Asegura que no se ingresen valores negativos
        help_text="Tasa de cambio de USD a CUP"
    )
    tasa_mlc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0)],  # Asegura que no se ingresen valores negativos
        help_text="Tasa de cambio de USD a MLC"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, help_text="Fecha de última actualización")

    activa = models.BooleanField(
        default=True,
        help_text="Indica si esta tasa de cambio está activa"
    )

    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ['-fecha_actualizacion']  # Ordena por la fecha de actualización, de la más reciente a la más antigua

    def __str__(self):
        return (f"Tasa de cambio (USD -> CUP): {self.tasa_cup:.4f}, "
                f"(USD -> MLC): {self.tasa_mlc:.4f} - "
                f"Actualizado el {self.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")

class Remesa(models.Model):
    nombre_remitente = models.CharField(max_length=255)
    documento_remitente = models.CharField(max_length=100)
    telefono_remitente = models.CharField(max_length=20)
    email_remitente = models.EmailField(blank=True, null=True)

    nombre_destinatario = models.CharField(max_length=255)
    telefono_destinatario = models.CharField(max_length=20)
    direccion_destinatario = models.TextField()

    monto_envio = models.DecimalField(max_digits=10, decimal_places=2)
    moneda_envio = models.CharField(max_length=3, choices=[('USD', 'Dólar estadounidense'), ('CUP', 'Peso cubano'), ('MLC', 'MLC')])
    monto_estimado_recepcion = models.DecimalField(max_digits=10, decimal_places=2)
    moneda_recepcion = models.CharField(max_length=3, choices=[('USD', 'Dólar estadounidense'), ('CUP', 'Peso cubano'), ('MLC', 'MLC')])

    def __str__(self):
        return f'Remesa {self.id} - {self.nombre_remitente} a {self.nombre_destinatario}'

class HabitacionReserva(models.Model):
    reserva = models.ForeignKey('Reserva', related_name='habitaciones_reserva', on_delete=models.CASCADE)
    habitacion_nombre = models.CharField(max_length=255)
    adultos = models.IntegerField()
    ninos = models.IntegerField()    
    fechas_viaje = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    oferta_codigo = models.CharField(max_length=50)

    def __str__(self):
        return f'Habitación {self.habitacion_nombre} - Reserva {self.reserva.id}'
    
class Pasajero(models.Model):
    habitacion = models.ForeignKey(HabitacionReserva, related_name='pasajeros', on_delete=models.CASCADE, blank=True, null=True)
    nombre = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    pasaporte = models.CharField(max_length=50, blank=True, null=True)
    caducidad_pasaporte = models.DateField(blank=True, null=True)
    pais_emision_pasaporte = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=1000, blank=True, null=True)
    estado_civil = models.CharField(max_length=10, choices=[('soltero', 'Soltero'), ('casado', 'Casado'), ('divorciado', 'Divorciado'), ('viudo', 'Viudo')], blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=[('adulto', 'Adulto'), ('nino', 'Niño')], blank=True, null=True)

    def __str__(self):
        return f'Pasajero {self.nombre} - Habitación {self.habitacion.habitacion_nombre}'

class OpcionCertificado(models.Model):
    nombre = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='opciones_certificados/', blank=True, null=True)
    descripcion = models.TextField()
    categoria = models.IntegerField(
        choices=[(i, f'{i} Estrellas') for i in range(1, 6)],  # Clasificación de 1 a 5 estrellas
        help_text="Clasificación de 1 a 5 estrellas"
    )
    
    def __str__(self):
        return f'{self.nombre} ({self.categoria} estrellas)'

class CertificadoVacaciones(models.Model):
    nombre = models.CharField(max_length=255, default="Certificado sin nombre")
    es_solo_adultos = models.BooleanField(default=False)
    pasajero = models.ForeignKey(Pasajero, on_delete=models.CASCADE, blank=True, null=True)
    opciones = models.ManyToManyField(OpcionCertificado, related_name='certificados')

    def __str__(self):
        return f'Certificado de Vacaciones - {self.nombre}'

class Reserva(models.Model):
    # Relaciones con otros modelos
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, blank=True, null=True)
    remesa = models.ForeignKey('Remesa', on_delete=models.CASCADE, blank=True, null=True)
    certificado_vacaciones = models.ForeignKey('CertificadoVacaciones', on_delete=models.CASCADE, blank=True, null=True)

    # Campos generales
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    nombre_usuario = models.CharField(max_length=255)
    email_empleado = models.EmailField()
    notas = models.TextField(blank=True, null=True)

    # Información de costos
    costo_sin_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Tipo de reserva
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('hoteles', 'Hoteles'),
            ('carros', 'Carros'),
            ('vuelos', 'Vuelos'),
            ('remesas', 'Remesas'),
            ('traslados', 'Traslados'),
            ('certificado', 'Certificado de Vacaciones'),
        ]
    )

    # Estatus de la reserva
    estatus = models.CharField(
        max_length=11,
        choices=[
            ('solicitada', 'Solicitada'),
            ('pendiente', 'Pendiente'),
            ('confirmada', 'Confirmada'),
            ('modificada', 'Modificada'),
            ('ejecutada', 'Ejecutada'),
            ('cancelada', 'Cancelada'),
            ('reembolsada', 'Reembolsada'),
        ]
    )

    # Información adicional
    numero_confirmacion = models.CharField(max_length=25, blank=True, null=True)
    cobrada = models.BooleanField(default=False)
    pagada = models.BooleanField(default=False)

    def esta_activa(self):
        """
        Verifica si la reserva está activa según su estatus.
        """
        return self.estatus in ['solicitada', 'pendiente', 'confirmada', 'modificada']

    def obtener_descripcion(self):
        """
        Genera una representación amigable de la reserva según su tipo.
        """
        if self.hotel:
            return f'Reserva {self.id} - Hotel: {self.hotel.hotel_nombre}'
        elif self.remesa:
            return f'Reserva {self.id} - Remesa de: {self.remesa.nombre_remitente}'
        elif self.certificado_vacaciones:
            return f'Reserva {self.id} - Certificado de Vacaciones'
        return f'Reserva {self.id} - Usuario: {self.nombre_usuario}'

     # Propiedad para calcular importe por cobrar
    @property
    def importe_por_cobrar(self):
        if self.cobrada:
            return Decimal('0.00')
        return self.costo_total  or Decimal('0.00')
    

    # Propiedad para calcular importe por pagar
    @property
    def importe_por_pagar(self):
        if self.pagada:
            return Decimal('0.00')
        return self.costo_sin_fee or Decimal('0.00')
    
    def __str__(self):
        """
        Devuelve una descripción representativa de la reserva.
        """
        return self.obtener_descripcion()

# =================
# Modelos de autos
# =================
class Rentadora(models.Model):
    nombre = models.CharField(max_length=255)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='rentadoras')

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=255)
    gasolina = models.CharField(max_length=100)
    rentadora = models.ForeignKey(Rentadora, on_delete=models.CASCADE, related_name='categorias')

    def __str__(self):
        return self.nombre

class ModeloAuto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='modelos_autos/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='modelos')

    def __str__(self):
        return self.nombre

class Location(models.Model):
    nombre = models.CharField(max_length=255)
    pais = models.CharField(max_length=100)
    nomenclatura = models.CharField(max_length=50)
    es_aeropuerto = models.BooleanField(default=False)
    disponibilidad_carros = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='locations')

    def __str__(self):
        return self.nombre

# =================
# Modelos Traslados
# =================

class Transportista(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.nombre

class Vehiculo(models.Model):
    TIPO_VEHICULO_CHOICES = [
        ('micro_10_plazas', 'Micro 10 Plazas (4 a 8 pax)'),
        ('bus_12_16_plazas', 'Bus 12-16 Plazas (9 a 14 pax)'),
        ('bus_24_29_plazas', 'Bus 24-29 Plazas (15 a 22 pax)'),
        ('omnibus_protocolo', 'Ómnibus Protocolo'),
        ('omnibus_34_plazas', 'Ómnibus 34 Plazas (23-32 Pax)'),
        ('omnibus_44_plazas', 'Ómnibus 44 Plazas (33-42 Pax)'),
        ('omnibus_48_plazas', 'Ómnibus 48 Plazas (43-46 Pax)'),
        
        ('auto_estandar', 'Auto estándar (1-2 Pax)'),
        ('auto_lujo', 'Auto Lujo (1-3 Pax)'),
        ('jeep', 'Jeep (1-4 Pax)'),        
        ('micro_1_5_pax', 'Micro (1-5 Pax)'),
        
        ('microbus_6_10_plazas', 'Microbús de 6-10 plazas (6-10 Pax)'),
        ('minibus_11_16_plazas', 'Minibús hasta 16 plazas (11-16 Pax)'),
        ('minibus_21_24_plazas', 'Minibús de 21-24 plazas (21-24 Pax)'),
        ('omnibus_41_49_plazas', 'Ómnibus de 41-49 plazas (41-49 Pax)'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPO_VEHICULO_CHOICES, unique=True)
    capacidad_min = models.PositiveIntegerField()
    capacidad_max = models.PositiveIntegerField()
    foto = models.ImageField(upload_to='fotos_vehiculos/', null=True, blank=True)

    def __str__(self):
        return dict(self.TIPO_VEHICULO_CHOICES).get(self.tipo, self.tipo)

class Traslado(models.Model):
    transportista = models.ForeignKey(Transportista, on_delete=models.CASCADE)
    origen = models.ForeignKey(Ubicacion, related_name='traslados_desde', on_delete=models.CASCADE)
    destino = models.ForeignKey(Ubicacion, related_name='traslados_hacia', on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('transportista', 'origen', 'destino', 'vehiculo')

    def __str__(self):
        return f"{self.transportista} - {self.origen} a {self.destino} ({self.vehiculo}): ${self.costo}"

