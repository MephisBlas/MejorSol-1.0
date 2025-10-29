from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.urls import path
from .models import Perfil, Producto

# Registrar el modelo User con personalización
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login']

# Re-registrar el modelo User con nuestra personalización
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_usuario', 'telefono', 'fecha_creacion']
    list_filter = ['tipo_usuario', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'telefono']
    readonly_fields = ['fecha_creacion']
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario', 'tipo_usuario')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion',)
        }),
    )

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'stock', 'activo', 'fecha_creacion']
    list_filter = ['categoria', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion', 'sku']
    list_editable = ['precio', 'stock', 'activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    list_per_page = 25
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'sku', 'categoria')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'stock', 'stock_minimo')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    # Eliminamos la función get_urls problemática por ahora
    # Puedes agregarla más tarde cuando necesites vistas personalizadas
    
    def producto_detalle_view(self, request, producto_id):
        """Vista para mostrar detalles del producto"""
        producto = get_object_or_404(Producto, id=producto_id)
        return render(request, 'admin/producto_detail.html', {'producto': producto})