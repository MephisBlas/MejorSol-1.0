import csv
from datetime import datetime
import json
import uuid
import random
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from .forms import RegistroForm, ProfileForm, ProductoForm  # ← SOLO ESTOS
from .models import ChatConversation, ChatMessage, Producto, Categoria
from . import models

# ===========================
# DECORADORES Y UTILIDADES
# ===========================

def is_admin(user):
    return user.is_staff or user.is_superuser

# ===========================
# VISTAS PÚBLICAS Y AUTENTICACIÓN
# ===========================

def index(request):
    return render(request, 'index.html')

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Registro exitoso! Bienvenido {user.first_name}.')
                return redirect('admin_panel' if (user.is_staff or user.is_superuser) else 'client_dashboard')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def form_valid(self, form):
        super().form_valid(form)
        return redirect('admin_panel' if (self.request.user.is_staff or self.request.user.is_superuser) else 'client_dashboard')

@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    return render(request, 'admin/admin_panel.html', {'user': request.user})

@login_required
def client_dashboard(request):
    return render(request, 'cliente/client_dashboard.html', {'user': request.user})

# ===========================
# VISTAS DE PRODUCTOS
# ===========================

@login_required
@user_passes_test(is_admin)
def productos_list(request):
    """Lista todos los productos"""
    productos = Producto.objects.all()
    
    # Filtros
    categoria = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    if categoria:
        productos = productos.filter(categoria__id=categoria)
    if estado:
        if estado == 'activo':
            productos = productos.filter(activo=True)
        elif estado == 'inactivo':
            productos = productos.filter(activo=False)
    
    categorias = Categoria.objects.filter(activo=True)
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'filtro_categoria': categoria,
        'filtro_estado': estado,
    }
    return render(request, 'admin/productos/productos_list.html', context)

@login_required
@user_passes_test(is_admin)
def producto_create(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('productos_list')
    else:
        form = ProductoForm()
    
    context = {'form': form, 'titulo': 'Nuevo Producto'}
    return render(request, 'admin/productos/producto_form.html', context)

@login_required
@user_passes_test(is_admin)
def producto_edit(request, pk):
    """Editar producto existente"""
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('productos_list')
    else:
        form = ProductoForm(instance=producto)
    
    context = {'form': form, 'titulo': 'Editar Producto', 'producto': producto}
    return render(request, 'admin/productos/producto_form.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def producto_delete(request, pk):
    """Eliminar producto"""
    producto = get_object_or_404(Producto, pk=pk)
    nombre_producto = producto.nombre
    producto.delete()
    messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
    return redirect('productos_list')

@login_required
@user_passes_test(is_admin)
def producto_detail(request, pk):
    """Detalle del producto"""
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'admin/productos/producto_detail.html', {'producto': producto})

# ===========================
# VISTAS DE INVENTARIO
# ===========================

@login_required
@user_passes_test(is_admin)
def control_inventario_view(request):
    """Vista principal de control de inventario"""
    productos = Producto.objects.select_related('categoria').all()
    
    # Filtros básicos
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if estado == 'bajo':
        productos = productos.filter(stock__lte=models.F('stock_minimo'))
    
    categorias = Categoria.objects.filter(activo=True)
    
    context = {
        'productos': productos,
        'categorias': categorias,
    }
    return render(request, 'admin/control_inventario.html', context)

# ===========================
# VISTAS DE COTIZACIONES (DEMO)
# ===========================

COTIZACIONES = [
    {"id": 1, "cliente": "Juan Pérez", "fecha": "2025-10-20", "total": 250000, "estado": "Pendiente"},
    {"id": 2, "cliente": "Empresa SolarTech", "fecha": "2025-10-21", "total": 480000, "estado": "Aprobada"},
]

@login_required
@user_passes_test(is_admin)
def cotizaciones_view(request):
    return render(request, "admin/cotizaciones.html", {"cotizaciones": COTIZACIONES})

@login_required
@user_passes_test(is_admin)
def crear_cotizacion(request):
    if request.method == "POST":
        # Lógica básica para crear cotización
        nuevo_id = len(COTIZACIONES) + 1
        COTIZACIONES.append({
            "id": nuevo_id,
            "cliente": request.POST.get("cliente", ""),
            "fecha": request.POST.get("fecha", ""),
            "total": request.POST.get("total", 0),
            "estado": "Pendiente"
        })
        return redirect("cotizaciones")
    return render(request, "admin/crear_cotizacion.html")

@login_required
@user_passes_test(is_admin)
def ver_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == int(cot_id)), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)
    return render(request, "admin/ver_cotizacion.html", {"cot": cot})

@login_required
@user_passes_test(is_admin)
def editar_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == int(cot_id)), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)
    
    if request.method == "POST":
        cot["cliente"] = request.POST.get("cliente", "")
        cot["fecha"] = request.POST.get("fecha", "")
        cot["total"] = request.POST.get("total", 0)
        cot["estado"] = request.POST.get("estado", "Pendiente")
        return redirect("cotizaciones")
    
    return render(request, "admin/editar_cotizacion.html", {"cot": cot})

@login_required
@user_passes_test(is_admin)
def eliminar_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == int(cot_id)), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)
    
    if request.method == "POST":
        COTIZACIONES.remove(cot)
        return redirect("cotizaciones")
    
    return render(request, "admin/eliminar_cotizacion.html", {"cot": cot})

# ===========================
# VISTAS DE REPORTES
# ===========================

def calculos_estadisticas_view(request):
    return render(request, 'admin/calculos_estadisticas.html')

def reportes_graficos_view(request):
    ventas_mensuales = [245680, 320000, 275400, 310200, 295000, 350000]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
    productos_stock = {"Transformadores": 30, "Paneles Solares": 55, "Baterías": 22, "Inversores": 18}

    context = {
        "meses": meses,
        "ventas": ventas_mensuales,
        "productos": list(productos_stock.keys()),
        "stock": list(productos_stock.values())
    }
    return render(request, "admin/reportes_graficos.html", context)

def historial_ventas_view(request):
    # Datos demo
    ventas_demo = [
        {"fecha": "2025-10-01", "numero": "F-00125", "cliente": "ElectroSur", "total": 245680, "estado": "Pagada"},
        {"fecha": "2025-09-28", "numero": "B-00987", "cliente": "EnerPlus", "total": 35680, "estado": "Pendiente"},
    ]
    
    context = {
        "ventas": ventas_demo,
        "demo": True,
    }
    return render(request, "admin/historial_ventas.html", context)

# ===========================
# VISTAS DE CUENTA
# ===========================

@login_required
def cuenta_view(request):
    user = request.user
    perfil_form = ProfileForm(instance=user)
    pass_form = PasswordChangeForm(user=user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            perfil_form = ProfileForm(request.POST, instance=user)
            if perfil_form.is_valid():
                perfil_form.save()
                messages.success(request, "Tu perfil se actualizó correctamente.")
                return redirect("cuenta")
        
        elif "change_password" in request.POST:
            pass_form = PasswordChangeForm(user=user, data=request.POST)
            if pass_form.is_valid():
                user = pass_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Tu contraseña se cambió correctamente.")
                return redirect("cuenta")

    return render(request, "admin/cuenta.html", {
        "perfil_form": perfil_form,
        "pass_form": pass_form,
    })

@login_required
def configuracion(request):
    return render(request, 'admin/configuracion.html')

# ===========================
# VISTAS DE CHATBOT (EXISTENTES)
# ===========================

def chatbot_demo(request):
    return render(request, 'chatbot/chatbot_demo.html')

@csrf_exempt
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Respuesta simple del chatbot
        bot_response = "Hola! Soy SIEERBot. Esta funcionalidad está en desarrollo."
        
        return JsonResponse({
            'status': 'success',
            'response': bot_response,
            'session_id': session_id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'response': 'Lo siento, ocurrió un error.',
            'error': str(e)
        })

def get_conversation_history(request, session_id):
    try:
        conv = ChatConversation.objects.get(session_id=session_id)
        msgs = ChatMessage.objects.filter(conversation=conv)
        history = [{'message': m.message, 'is_bot': m.is_bot, 'timestamp': m.timestamp.isoformat()} for m in msgs]
        return JsonResponse({'history': history})
    except ChatConversation.DoesNotExist:
        return JsonResponse({'history': []})

# ===========================
# MANEJO DE ERRORES
# ===========================

def handler_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler_500(request):
    return render(request, 'errors/500.html', status=500)



@login_required
@user_passes_test(is_admin)
def control_inventario_view(request):
    """Vista principal de control de inventario"""
    productos = Producto.objects.select_related('categoria').prefetch_related('imagenes').all()
    
    # Filtros
    q = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | 
            Q(sku__icontains=q) |
            Q(descripcion__icontains=q)
        )
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if estado:
        if estado == 'activo':
            productos = productos.filter(activo=True)
        elif estado == 'inactivo':
            productos = productos.filter(activo=False)
        elif estado == 'bajo':
            productos = productos.filter(stock__lte=models.F('stock_minimo'))
    
    # Exportar a CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['SKU', 'Producto', 'Categoría', 'Stock', 'Stock Mínimo', 'Precio', 'Estado'])
        
        for producto in productos:
            writer.writerow([
                producto.sku,
                producto.nombre,
                producto.categoria.nombre,
                producto.stock,
                producto.stock_minimo,
                producto.precio,
                'Bajo Stock' if producto.stock <= producto.stock_minimo else 'OK'
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(productos, 25)  # 25 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.filter(activo=True)
    
    context = {
        'productos': page_obj,
        'categorias': categorias,
    }
    return render(request, 'admin/control_inventario.html', context)