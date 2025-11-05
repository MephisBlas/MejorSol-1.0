# En: myapp/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
# 1. ¡CORRECCIÓN! AHORA IMPORTAMOS ProductoImagen
from .models import Perfil, Producto, Categoria, ChatConversation, ChatMessage, ProductoAdquirido, ProductoImagen
from .forms import ProductoAdquiridoForm

# ===========================
# ADMIN PERSONALIZADO DE USUARIO
# ===========================

class PerfilInline(admin.StackedInline):
    """Inline para el perfil en el admin de User"""
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'usuario'

class CustomUserAdmin(UserAdmin):
    """Admin personalizado para User con Perfil"""
    inlines = (PerfilInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'tipo_usuario']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'perfil__tipo_usuario']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'perfil__telefono']
    readonly_fields = ['date_joined', 'last_login']
    
    def tipo_usuario(self, obj):
        return obj.perfil.get_tipo_usuario_display() if hasattr(obj, 'perfil') else 'Sin perfil'
    tipo_usuario.short_description = 'Tipo de Usuario'

# Re-registrar User con admin personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ===========================
# ADMIN DE PERFILES
# ===========================

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_usuario', 'telefono', 'fecha_creacion']
    list_filter = ['tipo_usuario', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'telefono', 'direccion']
    readonly_fields = ['fecha_creacion']
    autocomplete_fields = ['usuario']
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario', 'tipo_usuario')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )

# ===========================
# ADMIN DE CATEGORÍAS
# ===========================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'fecha_creacion', 'productos_count']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo']
    readonly_fields = ['fecha_creacion']
    
    def productos_count(self, obj):
        return obj.producto_set.count()
    productos_count.short_description = 'Productos'

# ===========================
# 2. ¡CORRECCIÓN! AÑADIMOS LA CLASE INLINE PARA IMÁGENES
# (Esta es la clase que faltaba)
# ===========================
class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1  # Muestra 1 formulario vacío por defecto
    verbose_name = "Imagen del producto"
    verbose_name_plural = "Imágenes del producto"
    fields = ('imagen', 'orden', 'es_principal')


# ===========================
# ADMIN DE PRODUCTOS
# ===========================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'categoria', 'precio', 'stock', 
        'stock_minimo', 'necesita_reposicion', 'activo', 
        'fecha_creacion'
    ]
    list_filter = ['categoria', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion', 'sku']
    list_editable = ['precio', 'stock', 'stock_minimo', 'activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    autocomplete_fields = ['categoria']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'sku', 'categoria')
        }),
        ('Precios y Stock', {
            'fields': ('precio', 'stock', 'stock_minimo')
        }),
        ('Estado del Producto', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    # 3. ¡CORRECCIÓN! AÑADIMOS LA LÍNEA 'inlines'
    # (Esta línea conecta las imágenes con el producto)
    inlines = [ProductoImagenInline]
    
    def necesita_reposicion(self, obj):
        return obj.stock <= obj.stock_minimo
    necesita_reposicion.boolean = True
    necesita_reposicion.short_description = 'Stock Bajo'

# ===========================
# ADMIN DE CHATBOT
# ===========================

@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_id']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'message_preview', 'is_bot', 'timestamp']
    list_filter = ['is_bot', 'timestamp']
    search_fields = ['conversation__session_id', 'message']
    readonly_fields = ['timestamp']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mensaje'

# ===========================
# CONFIGURACIÓN GLOBAL DEL ADMIN
# ===========================

admin.site.site_header = 'SIEER Chile - Administración'
admin.site.site_title = 'SIEER Chile Admin'
admin.site.index_title = 'Panel de Administración'

@admin.register(ProductoAdquirido)
class ProductoAdquiridoAdmin(admin.ModelAdmin):
    form = ProductoAdquiridoForm
    list_display = ['cliente', 'producto', 'precio_adquisicion', 'fecha_compra', 'garantia_activa']
    list_filter = ['fecha_compra', 'estado_garantia']
    search_fields = ['cliente__username', 'producto__nombre']