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
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .forms import RegistroForm, ProfileForm, ProductoForm
from .models import ChatConversation, ChatMessage, Producto, Categoria, ProductoAdquirido


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
    
    def get_success_url(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return reverse('admin_panel')
        else:
            return reverse('client_dashboard')


@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    """Vista principal del panel administrativo"""
    productos = Producto.objects.select_related('categoria').all().order_by('-fecha_creacion')[:10]
    
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | 
            Q(sku__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if estado == 'bajo':
        productos = productos.filter(stock__lte=F('stock_minimo'))
    elif estado == 'inactivo':
        productos = productos.filter(activo=False)
    elif estado == 'activo':
        productos = productos.filter(activo=True)
    
    if request.GET.get('export') == 'csv':
        return export_inventario_csv(Producto.objects.all())
    
    categorias = Categoria.objects.filter(activo=True)
    total_productos = Producto.objects.count()
    
    context = {
        'user': request.user,
        'productos': productos,
        'categorias': categorias,
        'total_productos': total_productos,
    }
    return render(request, 'admin/admin_panel.html', context)

@login_required
def client_dashboard(request):
    return render(request, 'cliente/client_dashboard.html', {'user': request.user})


# ===========================
# VISTA PRINCIPAL DE CONTROL INVENTARIO - TODO INTEGRADO
# ===========================

@login_required
@user_passes_test(is_admin)
def control_inventario_view(request):
    """Vista principal de control de inventario - TODO INTEGRADO"""
    # Verificar si es una acción específica
    action = request.GET.get('action')
    producto_id = request.GET.get('producto_id')
    
    # FORMULARIO DE CREAR/EDITAR PRODUCTO
    if action in ['crear', 'editar']:
        if action == 'editar' and producto_id:
            producto = get_object_or_404(Producto, pk=producto_id)
            form = ProductoForm(instance=producto)
            titulo = f'Editar Producto - {producto.nombre}'
        else:
            form = ProductoForm()
            titulo = 'Nuevo Producto'
        
        # Procesar formulario si es POST
        if request.method == 'POST':
            if action == 'editar' and producto_id:
                producto = get_object_or_404(Producto, pk=producto_id)
                form = ProductoForm(request.POST, instance=producto)
            else:
                form = ProductoForm(request.POST)
            
            if form.is_valid():
                producto = form.save(commit=False)
                if action == 'crear':
                    producto.usuario_creacion = request.user
                producto.save()
                messages.success(request, f'Producto "{producto.nombre}" guardado exitosamente.')
                return redirect('control_inventario')
        
        context = {
            'mostrar_formulario': True,
            'form': form,
            'titulo': titulo,
            'action': action,
        }
        return render(request, 'admin/control_inventario.html', context)
    
    # DETALLES DE PRODUCTO
    if action == 'detalle' and producto_id:
        producto = get_object_or_404(Producto, pk=producto_id)
        context = {
            'mostrar_detalles': True,
            'producto': producto,
        }
        return render(request, 'admin/control_inventario.html', context)
    
    # MOVIMIENTO DE INVENTARIO
    if action == 'movimiento' and producto_id:
        producto = get_object_or_404(Producto, pk=producto_id)
        
        if request.method == 'POST':
            tipo_movimiento = request.POST.get('tipo_movimiento')
            cantidad = int(request.POST.get('cantidad', 0))
            observaciones = request.POST.get('observaciones', '')
            
            if tipo_movimiento == 'ENTRADA':
                producto.stock += cantidad
                messages.success(request, f'Entrada de {cantidad} unidades registrada para {producto.nombre}')
            elif tipo_movimiento == 'SALIDA':
                if producto.stock >= cantidad:
                    producto.stock -= cantidad
                    messages.success(request, f'Salida de {cantidad} unidades registrada para {producto.nombre}')
                else:
                    messages.error(request, f'Stock insuficiente para {producto.nombre}')
                    return redirect('control_inventario')
            
            producto.save()
            return redirect('control_inventario')
        
        context = {
            'mostrar_movimiento': True,
            'producto': producto,
        }
        return render(request, 'admin/control_inventario.html', context)
    
    # MODO NORMAL: LISTA DE PRODUCTOS
    productos = Producto.objects.select_related('categoria').all().order_by('-fecha_creacion')
    
    # Aplicar filtros
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | 
            Q(sku__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if estado == 'bajo':
        productos = productos.filter(stock__lte=F('stock_minimo'))
    elif estado == 'inactivo':
        productos = productos.filter(activo=False)
    elif estado == 'activo':
        productos = productos.filter(activo=True)
    
    # Exportar a CSV
    if request.GET.get('export') == 'csv':
        return export_inventario_csv(productos)
    
    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.filter(activo=True)
    
    context = {
        'productos': page_obj,
        'categorias': categorias,
        'mostrar_lista': True,
    }
    return render(request, 'admin/control_inventario.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def producto_delete(request, pk):
    """Eliminar producto"""
    producto = get_object_or_404(Producto, pk=pk)
    nombre_producto = producto.nombre
    producto.delete()
    messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
    return redirect('control_inventario')


def export_inventario_csv(queryset):
    """Función para exportar inventario a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['SKU', 'Producto', 'Categoría', 'Stock', 'Stock Mínimo', 'Precio', 'Estado'])
    
    for producto in queryset:
        estado = 'OK'
        if producto.stock <= producto.stock_minimo:
            estado = 'BAJO STOCK'
        elif not producto.activo:
            estado = 'INACTIVO'
            
        writer.writerow([
            producto.sku,
            producto.nombre,
            producto.categoria.nombre if producto.categoria else '',
            producto.stock,
            producto.stock_minimo,
            producto.precio,
            estado
        ])
    
    return response


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

@login_required
@user_passes_test(is_admin)
def calculos_estadisticas_view(request):
    return render(request, 'admin/calculos_estadisticas.html')


@login_required
@user_passes_test(is_admin)
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


@login_required
@user_passes_test(is_admin)
def historial_ventas_view(request):
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
# VISTAS DE CHATBOT
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

def client_dashboard(request):
    productos_adquiridos = ProductoAdquirido.objects.filter(cliente=request.user).select_related('producto')
    
    context = {
        'user': request.user,
        'productos_adquiridos': productos_adquiridos,
    }
    return render(request, 'cliente/client_dashboard.html', context)