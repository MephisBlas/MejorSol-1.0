from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Categoria, Producto
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

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

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']
    list_per_page = 20



@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'stock', 'activo', 'fecha_creacion']
    list_filter = ['categoria', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
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
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('detalle/<int:producto_id>/', 
                 self.admin_site.admin_view(self.producto_detalle_view),
                 name='myapp_producto_detalle'),
        ]
        return custom_urls + urls
    
    def producto_detalle_view(self, request, producto_id):
        """Vista para mostrar detalles del producto en modal"""
        producto = get_object_or_404(Producto, id=producto_id)
        
        # Si es una petición AJAX, retornar solo el template del detalle
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'admin/producto_detail.html', {'producto': producto})
        
        # Para peticiones normales, también funciona
        return render(request, 'admin/producto_detail.html', {'producto': producto})