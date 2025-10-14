from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Categoria, Producto

# Registrar el modelo User con personalización
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login']

# Re-registrar el modelo User con nuestra personalización
admin.site.unregister(User)  # Desregistrar el default
admin.site.register(User, CustomUserAdmin)  # Registrar con nuestra clase

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_usuario', 'telefono', 'fecha_creacion']
    list_filter = ['tipo_usuario', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'telefono']
    readonly_fields = ['fecha_creacion']
    
    # Para mostrar más información del usuario en el detalle
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
    readonly_fields = ['fecha_creacion']
    list_per_page = 25
    
    # Para mostrar imagen en el admin (si usas ImageField)
    # readonly_fields = ['imagen_preview']
    # 
    # def imagen_preview(self, obj):
    #     if obj.imagen:
    #         return mark_safe(f'<img src="{obj.imagen.url}" width="100" />')
    #     return "No image"
    # imagen_preview.short_description = 'Vista Previa'