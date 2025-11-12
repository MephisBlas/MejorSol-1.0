from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone
import os
import uuid

# ===========================
# MODELOS DE USUARIO Y PERFIL
# ===========================

class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='cliente')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        db_table = 'perfiles'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_usuario_display()}"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Señal para crear perfil automáticamente al crear usuario"""
    if created:
        Perfil.objects.get_or_create(usuario=instance)

# ===========================
# MODELOS DE CHATBOT (GENERAL AI)
# ===========================

class ChatConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Conversación de Chat IA'
        verbose_name_plural = 'Conversaciones de Chat IA'
        ordering = ['-created_at']

class ChatMessage(models.Model):
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    is_bot = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Mensaje de Chat IA'
        verbose_name_plural = 'Mensajes de Chat IA'
        ordering = ['timestamp']

# ===========================
# MODELOS DE CATALOGO E INVENTARIO
# ===========================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de Categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        db_table = 'categorias'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('agotado', 'Agotado'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU Único")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name="Categoría")
    
    precio = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Precio de Venta")
    costo = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0, verbose_name="Costo de Compra")
    stock = models.IntegerField(validators=[MinValueValidator(0)], verbose_name="Stock Disponible", default=0)
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)], verbose_name="Stock Mínimo de Seguridad")
    
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    activo = models.BooleanField(default=True, verbose_name="Activo en Sistema")
    
    potencia = models.CharField(max_length=50, blank=True, verbose_name="Potencia")
    voltaje = models.CharField(max_length=50, blank=True, verbose_name="Voltaje")
    dimensiones = models.CharField(max_length=100, blank=True, verbose_name="Dimensiones")
    icono = models.CharField(max_length=50, default='box', verbose_name="Icono FontAwesome")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_creados')
    
    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.sku}"
    
    @property
    def necesita_reposicion(self):
        return self.stock <= self.stock_minimo
    
    @property
    def margen_ganancia(self):
        if self.costo > 0:
            return ((self.precio - self.costo) / self.costo) * 100
        return 0


def upload_to_producto_path(instance, filename):
    """Función para generar ruta de upload dinámica"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"productos/{instance.producto.sku}/{filename}"

class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to=upload_to_producto_path, verbose_name="Archivo de Imagen")
    orden = models.IntegerField(default=0, verbose_name="Orden de Visualización")
    es_principal = models.BooleanField(default=False, verbose_name="Imagen Principal")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Producto'
        ordering = ['-es_principal', 'orden']
        db_table = 'producto_imagenes'
    
    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
    ]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField(verbose_name="Cantidad Movida")
    cantidad_anterior = models.IntegerField(verbose_name="Stock Anterior")
    cantidad_nueva = models.IntegerField(verbose_name="Stock Nuevo")
    referencia = models.CharField(max_length=100, blank=True, verbose_name="Número de Referencia")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Usuario Responsable")
    fecha_movimiento = models.DateTimeField(default=timezone.now)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        db_table = 'movimientos_inventario'
        ordering = ['-fecha_movimiento']

# ===========================
# MODELO DE PRODUCTOS ADQUIRIDOS
# ===========================

class ProductoAdquirido(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos_adquiridos')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    precio_adquisicion = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio de Adquisición")
    fecha_compra = models.DateField(default=timezone.now, verbose_name="Fecha de Compra")
    fecha_instalacion = models.DateField(null=True, blank=True, verbose_name="Fecha de Instalación")
    garantia_meses = models.IntegerField(default=12, verbose_name="Meses de Garantía")
    estado_garantia = models.CharField(
        max_length=20,
        choices=[
            ('activa', 'Garantía Activa'),
            ('expirada', 'Garantía Expirada'),
            ('usada', 'Garantía Usada')
        ],
        default='activa'
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    class Meta:
        verbose_name = 'Producto Adquirido'
        verbose_name_plural = 'Productos Adquiridos'
        db_table = 'productos_adquiridos'
        ordering = ['-fecha_compra']
        unique_together = ['cliente', 'producto', 'fecha_compra']
    
    def __str__(self):
        return f"{self.cliente.username} - {self.producto.nombre}"
    
    @property
    def garantia_expira(self):
        if self.fecha_compra:
            return self.fecha_compra + timezone.timedelta(days=self.garantia_meses * 30)
        return None
    
    @property
    def garantia_activa(self):
        if self.estado_garantia == 'expirada':
            return False
        expira_fecha = self.garantia_expira
        if expira_fecha and expira_fecha < timezone.now().date():
            self.estado_garantia = 'expirada'
            self.save()
            return False
        return self.estado_garantia == 'activa'

# ===========================
# MODELO DE INSTALACIONES (PROYECTOS) - HU-H09 <<<--- MOVIDO AQUÍ PARA RESOLVER NameError
# ===========================

class Instalacion(models.Model):
    ESTADO_PROYECTO_CHOICES = [
        ('cotizado', 'Cotizado / Pendiente de Aprobación'),
        ('aprobado', 'Aprobado / Esperando Inicio'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado / Entregado'),
        ('garantia', 'En Garantía'),
        ('cancelado', 'Cancelado'),
    ]

    # Datos clave de la relación (ForeignKey)
    cliente = models.ForeignKey(User, on_delete=models.PROTECT, related_name='instalaciones_cliente', verbose_name="Cliente Asociado")
    # AHORA PRODUCTOADQUIRIDO EXISTE, POR LO QUE ESTA LÍNEA FUNCIONARÁ:
    producto_adquirido = models.ForeignKey(ProductoAdquirido, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto Adquirido")
    
    # Datos del proyecto
    nombre_proyecto = models.CharField(max_length=255, verbose_name="Nombre o Código del Proyecto", unique=True)
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio Estimada", default=timezone.now)
    fecha_termino_estimada = models.DateField(verbose_name="Fecha de Término Estimada", null=True, blank=True)
    fecha_termino_real = models.DateField(verbose_name="Fecha de Término Real", null=True, blank=True)
    
    # Datos de gestión y estado
    estado = models.CharField(max_length=20, choices=ESTADO_PROYECTO_CHOICES, default='cotizado', verbose_name="Estado Actual")
    observaciones = models.TextField(blank=True, verbose_name="Notas del Administrador")
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo Total Estimado")

    class Meta:
        verbose_name = 'Instalación (Proyecto)'
        verbose_name_plural = 'Instalaciones (Proyectos)'
        db_table = 'instalaciones_proyectos'
        ordering = ['estado', '-fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre_proyecto} - {self.get_estado_display()}"


# ===========================
# MODELOS DE COTIZACIÓN (FORMULARIO ANTIGUO)
# ===========================
# NOTA: Estos modelos se dejan aquí ya que no dependen de Instalacion.

class Cotizacion(models.Model):
    ESTADO_COTIZACION_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('expirada', 'Expirada'),
    ]
    cliente_nombre = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    cliente_rut = models.CharField(max_length=12, blank=True, verbose_name="RUT del Cliente")
    cliente_email = models.EmailField(blank=True, verbose_name="Email del Cliente")
    cliente_telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono del Cliente")
    numero_cotizacion = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número de Cotización")
    fecha_emision = models.DateField(default=timezone.now, verbose_name="Fecha de Emisión")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento", null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_COTIZACION_CHOICES, default='borrador')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, verbose_name="Observaciones Internas")
    notas_cliente = models.TextField(blank=True, verbose_name="Notas para el Cliente")
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cotizaciones')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Cotización (Formulario)'
        verbose_name_plural = 'Cotizaciones (Formulario)'
        db_table = 'cotizaciones_formulario'
        ordering = ['-fecha_emision']
    def __str__(self):
        return f"Cotización (Form) #{self.id} - {self.cliente_nombre}"

class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    class Meta:
        db_table = 'items_cotizacion'
        verbose_name = 'Item de Cotización'
        verbose_name_plural = 'Items de Cotización'

# ===========================
# ¡NUEVO! MODELOS PARA CHAT DE COTIZACIÓN
# ===========================

class ChatCotizacion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Admin'),
        ('en_proceso', 'En Proceso'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='chats_cotizacion')
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_cotizacion')
    admin_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones_asignadas')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    cliente_nombre_dato = models.CharField(max_length=255, blank=True, null=True)
    cliente_email_dato = models.EmailField(blank=True, null=True)
    cliente_telefono_dato = models.CharField(max_length=20, blank=True, null=True)
    cliente_rut_dato = models.CharField(max_length=20, blank=True, null=True)
    cliente_mensaje_dato = models.TextField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Chat de Cotización'
        verbose_name_plural = 'Chats de Cotizaciones'
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"Cotización #{self.id} de {self.cliente.username} por {self.producto.nombre}"

class MensajeCotizacion(models.Model):
    chat = models.ForeignKey(ChatCotizacion, on_delete=models.CASCADE, related_name='mensajes')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    es_bot = models.BooleanField(default=False)
    
    mensaje = models.TextField()
    imagen = models.ImageField(upload_to='cotizaciones_img/', blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje de Cotización'
        verbose_name_plural = 'Mensajes de Cotizaciones'
        ordering = ['timestamp']

    def __str__(self):
        return f"Mensaje de {self.autor.username} en chat #{self.chat.id}"