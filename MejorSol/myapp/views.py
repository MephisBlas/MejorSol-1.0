import csv
import re
import json
import uuid
from datetime import datetime, timedelta # IMPORT CORREGIDO
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum, Count, ProtectedError, Avg # IMPORT CORREGIDO
from django.db.models.functions import TruncMonth, TruncDay # IMPORT CORREGIDO
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ClienteProfileForm # Import limpio

# --- Formularios ---
from .forms import (
    RegistroForm, ProfileForm, ProductoForm, 
    ProductoAdquiridoForm, ProductoImagenFormSet
)
# --- Modelos ---
from .models import (
    ChatConversation, ChatMessage, Producto, Categoria, 
    ProductoAdquirido, ProductoImagen, Cotizacion, ItemCotizacion,
    ChatCotizacion, MensajeCotizacion, Perfil
)
# --- Servicios ---
from .services import ChatBotService 

# --- ¡LIBRERÍAS DE MACHINE LEARNING! ---
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
# ---------------------------------------


# ===========================
# DECORADORES Y UTILIDADES (¡REPARADO!)
# ===========================

def is_admin(user):
    return user.is_staff or user.is_superuser

def is_admin_or_vendedor(user):
    """Verifica si el usuario es administrador, superusuario o vendedor (por perfil)."""
    # 1. Si es staff o superuser de Django, SIEMPRE tiene acceso (REPARACIÓN CLAVE).
    if user.is_staff or user.is_superuser:
         return True
    
    # 2. Si no es staff, verifica si tiene el perfil correcto.
    return user.is_authenticated and hasattr(user, 'perfil') and (user.perfil.tipo_usuario in ['admin', 'vendedor', 'superuser'])

def is_cliente(user):
    """Verifica si el usuario es un cliente."""
    return user.is_authenticated and hasattr(user, 'perfil') and (user.perfil.tipo_usuario == 'cliente')


# ===========================
# VISTAS PÚBLICAS Y AUTENTICACIÓN
# ===========================

def index(request):
    # --- ARREGLO DE REDIRECCIÓN ---
    # 1. Verifica si el usuario ya está conectado
    if request.user.is_authenticated:
        
        # 2. Si es admin/staff, llévalo al panel de admin
        if request.user.is_staff or request.is_superuser:
            return redirect('admin_panel') # Asegúrate que 'admin_panel' es el nombre en tu urls.py
        
        # 3. Si es cualquier otro usuario (cliente), llévalo al panel de cliente
        else:
            return redirect('client_dashboard') # Asegúrate que 'client_dashboard' es el nombre en tu urls.py

    # 4. Si no está conectado, recién ahí le muestras la landing page
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


# ===========================
# VISTA DEL DASHBOARD (ADMIN)
# ===========================

@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    """
    Vista principal del panel administrativo con KPIs dinámicos
    y actividad reciente.
    """
    
    # --- 1. Datos para las tarjetas (KPIs) ---
    now = timezone.now()
    
    # KPI 1: Cotizaciones del Mes (Tu solicitud)
    kpi_cotizaciones_mes = ChatCotizacion.objects.filter(
        fecha_creacion__year=now.year,
        fecha_creacion__month=now.month
    ).count()

    # KPI 2: Productos Registrados (Tu solicitud)
    kpi_total_productos = Producto.objects.count()

    # KPI 3: Clientes Registrados (Tu solicitud)
    kpi_total_clientes = Perfil.objects.filter(tipo_usuario='cliente').count()

    # KPI 4: Stock Total (Tu solicitud)
    stock_data = Producto.objects.aggregate(total_stock=Sum('stock'))
    kpi_stock_total = stock_data['total_stock'] or 0 # 'or 0' si no hay productos
    
    # --- 2. Datos para "Actividad Reciente" (¡También dinámico!) ---
    act_cotizaciones = ChatCotizacion.objects.select_related('cliente', 'producto').order_by('-fecha_creacion')[:3]
    act_productos = Producto.objects.select_related('categoria').order_by('-fecha_creacion')[:2]
    act_clientes = Perfil.objects.select_related('usuario').filter(tipo_usuario='cliente').order_by('-fecha_creacion')[:2]

    # --- 3. Enviar todo al template ---
    context = {
        'user': request.user,
        
        # Enviar KPIs
        'kpi_cotizaciones_mes': kpi_cotizaciones_mes,
        'kpi_total_productos': kpi_total_productos,
        'kpi_total_clientes': kpi_total_clientes,
        'kpi_stock_total': kpi_stock_total,
        
        # Enviar Actividad Reciente
        'act_cotizaciones': act_cotizaciones,
        'act_productos': act_productos,
        'act_clientes': act_clientes,
    }
    return render(request, 'admin/admin_panel.html', context)


# ===========================
# VISTA DE INVENTARIO
# ===========================

@login_required
@user_passes_test(is_admin)
def control_inventario_view(request):
    """Vista principal de control de inventario - TODO INTEGRADO"""
    action = request.GET.get('action')
    producto_id = request.GET.get('producto_id')
    
    # --- FORMULARIO DE CREAR/EDITAR PRODUCTO ---
    if action in ['crear', 'editar']:
        
        if action == 'editar' and producto_id:
            producto = get_object_or_404(Producto, pk=producto_id)
            titulo = f'Editar Producto - {producto.nombre}'
        else:
            producto = Producto()
            titulo = 'Nuevo Producto'
        
        if request.method == 'POST':
            # FIX DE IMAGEN: Se asegura que el form y el formset reciban request.FILES
            form = ProductoForm(request.POST, request.FILES, instance=producto)
            formset = ProductoImagenFormSet(request.POST, request.FILES, instance=producto)
            
            if form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():
                        producto_guardado = form.save(commit=False)
                        if action == 'crear':
                            producto_guardado.usuario_creacion = request.user
                        producto_guardado.save()
                        
                        formset.instance = producto_guardado
                        formset.save()
                        
                        messages.success(request, f'Producto "{producto_guardado.nombre}" guardado exitosamente.')
                        return redirect('control_inventario')
                except Exception as e:
                    messages.error(request, f'Error al guardar el producto: {e}')
            else:
                 messages.error(request, 'Por favor, corrige los errores en el formulario.')

        else:
            form = ProductoForm(instance=producto)
            formset = ProductoImagenFormSet(instance=producto)
        
        context = {
            'mostrar_formulario': True,
            'form': form,
            'formset': formset,
            'titulo': titulo,
            'action': action,
        }
        return render(request, 'admin/control_inventario.html', context)
    
    # --- DETALLES DE PRODUCTO / MOVIMIENTO (Lógica simplificada) ---
    if action == 'detalle' and producto_id:
        producto = get_object_or_404(Producto, pk=producto_id)
        context = {'mostrar_detalles': True, 'producto': producto}
        return render(request, 'admin/control_inventario.html', context)
    
    if action == 'movimiento' and producto_id:
        producto = get_object_or_404(Producto, pk=producto_id)
        context = {'mostrar_movimiento': True, 'producto': producto}
        return render(request, 'admin/control_inventario.html', context)
    
    # --- MODO NORMAL: LISTA DE PRODUCTOS ---
    # Lógica de filtrado para el inventario - AÑADIDA para coincidir con el HTML
    q = request.GET.get('q')
    categoria = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    productos = Producto.objects.select_related('categoria').all()

    if q:
        productos = productos.filter(Q(sku__icontains=q) | Q(nombre__icontains=q))
    
    if categoria:
        productos = productos.filter(categoria__id=categoria)
        
    if estado == 'activo':
        productos = productos.filter(activo=True)
    elif estado == 'inactivo':
        productos = productos.filter(activo=False)
    elif estado == 'bajo':
        # Filtra productos con stock <= stock_minimo Y activo=True
        productos = productos.filter(stock__lte=F('stock_minimo'), activo=True, stock__gt=0)


    productos = productos.order_by('-fecha_creacion')
    
    if request.GET.get('export') == 'csv':
        return export_inventario_csv(productos)
    
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


# ===========================
# VISTA DE ELIMINAR PRODUCTO (¡¡FIXED!!)
# ===========================
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    nombre_producto = producto.nombre
    
    # Contamos si este producto tiene chats o productos adquiridos (que también podrían protegerlo)
    chat_count = ChatCotizacion.objects.filter(producto=producto).count()
    adquirido_count = ProductoAdquirido.objects.filter(producto=producto).count()

    if chat_count > 0 or adquirido_count > 0:
        # Si hay chats o ventas, no podemos borrar. Lo desactivamos.
        try:
            producto.activo = False
            producto.save()
            messages.warning(request, f'El producto "{nombre_producto}" no se puede eliminar porque tiene {chat_count} chats y {adquirido_count} ventas asociadas. En su lugar, ha sido marcado como "Inactivo".')
        except Exception as e:
            messages.error(request, f'Error al intentar desactivar el producto: {e}')
    else:
        # Si no hay chats NI ventas, intentamos borrarlo.
        try:
            producto.delete()
            messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente (no tenía chats ni ventas).')
        except ProtectedError as e:
            # Catch por si OTRA cosa (que no revisamos) lo protege
            messages.error(request, f'Error: No se pudo eliminar "{nombre_producto}". Está protegido por otras relaciones: {e}')
        except Exception as e:
            messages.error(request, f'Error inesperado al eliminar: {e}')
            
    return redirect('control_inventario')


def export_inventario_csv(queryset):
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
            producto.sku, producto.nombre,
            producto.categoria.nombre if producto.categoria else '',
            producto.stock, producto.stock_minimo, producto.precio, estado
        ])
    return response


# ===========================
# VISTAS DE COTIZACIONES (PARA ADMINS / VENDEDORES - ¡REPARADO!)
# ===========================

@login_required
@user_passes_test(is_admin_or_vendedor, login_url='/client-dashboard/')
def admin_lista_chats_cotizacion_view(request):
    """Muestra la lista de todos los chats de cotización para el Admin/Vendedor."""
    
    ESTADO_DB_CHOICES = ['pendiente', 'en_proceso', 'aprobada', 'rechazada']
    estado_filtro = request.GET.get('estado')
    
    chats = ChatCotizacion.objects.all().select_related('cliente', 'producto').order_by('-fecha_actualizacion')
    
    if estado_filtro and estado_filtro != 'todos' and estado_filtro in ESTADO_DB_CHOICES:
        chats = chats.filter(estado=estado_filtro)

    contadores = {
        'todos': ChatCotizacion.objects.all().count(),
        'pendiente': ChatCotizacion.objects.filter(estado='pendiente').count(),
        'en_proceso': ChatCotizacion.objects.filter(estado='en_proceso').count(),
        'aprobada': ChatCotizacion.objects.filter(estado='aprobada').count(),
        'rechazada': ChatCotizacion.objects.filter(estado='rechazada').count(),
    }
    
    context = {
        'chats_cotizacion': chats, 
        'filtro_actual': estado_filtro if estado_filtro else 'todos',
        'contadores': contadores,
    }
    
    return render(request, 'admin/cotizaciones.html', context)


@xframe_options_sameorigin
@login_required
@user_passes_test(is_admin_or_vendedor, login_url='/client-dashboard/')
def admin_chat_cotizacion_view(request, chat_id):
    """Muestra el detalle de un chat de cotización para el Admin/Vendedor."""
    chat = get_object_or_404(ChatCotizacion, id=chat_id)
    
    chat_api_url = reverse('chat_api_view', kwargs={'chat_id': chat.id}) 
            
    context = {
        'chat': chat,
        'is_admin_view': True,
        'chat_api_url': chat_api_url,
        'chat_estados': ChatCotizacion.ESTADO_CHOICES 
    }
    # Usa el template compartido 'chat_detail.html'
    return render(request, 'chat/chat_detail.html', context)


# --- Vistas de Redirección Antiguas (Redirección correcta para evitar ciclos) ---

@login_required
@user_passes_test(is_admin)
def cotizaciones_view(request):
    """ ¡REPARADO! Redirección directa al listado principal. """
    # Esta es la que causaba el ciclo si estaba en urls.py con el mismo nombre.
    return redirect('admin_lista_chats_cotizacion') # Redirige a admin_lista_chats_cotizacion_view


@login_required
@user_passes_test(is_admin)
def crear_cotizacion(request):
    """ Crea una nueva cotización MANUALMENTE. """
    messages.info(request, "Esta función es para crear cotizaciones manualmente.")
    return render(request, "admin/crear_cotizacion.html")


@login_required
@user_passes_test(is_admin)
def ver_cotizacion(request, cot_id):
    """ Redirige al chat para ver/gestionar la cotización. """
    return redirect('admin_chat_cotizacion', chat_id=cot_id)


@login_required
@user_passes_test(is_admin)
def editar_cotizacion(request, cot_id):
    """ Redirige al chat para editar/gestionar la cotización. """
    return redirect('admin_chat_cotizacion', chat_id=cot_id)


@login_required
@user_passes_test(is_admin)
def eliminar_cotizacion(request, cot_id):
    chat = get_object_or_404(ChatCotizacion, id=cot_id)
    
    if request.method == "POST":
        chat.delete()
        messages.success(request, f"Cotización #{cot_id} eliminada.")
        return redirect("cotizaciones")
    
    context = { 'cot': chat }
    return render(request, "admin/eliminar_cotizacion.html", context)


# ===========================
# VISTAS DE REPORTES, CUENTA, Y CHATBOT GENERAL
# ===========================

@login_required
@user_passes_test(is_admin)
def calculos_estadisticas_view(request):
    total_ventas = ProductoAdquirido.objects.aggregate(total=Sum('precio_adquisicion'))['total'] or 0
    total_clientes = ProductoAdquirido.objects.values('cliente').distinct().count()
    total_productos = Producto.objects.filter(activo=True).count()
    
    context = {
        'total_ventas': total_ventas,
        'total_clientes': total_clientes,
        'total_productos': total_productos,
    }
    return render(request, 'admin/calculos_estadisticas.html', context)


# ================================================================
# VISTA DE REPORTES GRÁFICOS (BI + ML) - ¡¡AQUÍ ESTÁ LA ACTUALIZACIÓN!!
# ================================================================
@login_required
@user_passes_test(is_admin)
def reportes_graficos_view(request):
    """
    NUEVA VISTA TIPO POWER BI
    Calcula KPIs de BI y una predicción de ML.
    """
    
    # --- 1. KPIs de BI (Tus datos reales) ---
    total_cotizaciones = ChatCotizacion.objects.count()
    aprobadas = ChatCotizacion.objects.filter(estado='aprobada').count()
    
    # Tasa de Conversión
    tasa_conversion = (aprobadas / total_cotizaciones * 100) if total_cotizaciones > 0 else 0
    
    # Promedio de cotizaciones por día (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    cotizaciones_30_dias = ChatCotizacion.objects.filter(fecha_creacion__gte=hace_30_dias).count()
    promedio_cot_dia = cotizaciones_30_dias / 30.0

    # --- 2. Datos para Gráficos de BI (Tus datos reales) ---
    
    # Gráfico Embudo (Dona)
    embudo_data = ChatCotizacion.objects.values('estado').annotate(total=Count('estado')).order_by('-total')
    # Usamos el display name de tus CHOICES en el modelo para que sea legible
    embudo_labels = [dict(ChatCotizacion.ESTADO_CHOICES).get(item['estado'], 'N/A') for item in embudo_data]
    embudo_valores = [item['total'] for item in embudo_data]

    # Gráfico Productos (Barras)
    productos_data = ChatCotizacion.objects.values('producto__nombre').annotate(total=Count('id')).order_by('-total')[:7]
    productos_labels = [item['producto__nombre'] for item in productos_data if item['producto__nombre']]
    productos_valores = [item['total'] for item in productos_data if item['producto__nombre']]

    # --- 3. ¡¡INICIO DE MACHINE LEARNING!! (Predicción de Demanda) ---
    
    # 3.1. Obtener datos históricos (los últimos 90 días para entrenar)
    hace_90_dias = timezone.now() - timedelta(days=90)
    tendencia_data_historica = ChatCotizacion.objects.filter(
        fecha_creacion__gte=hace_90_dias
    ).annotate(
        dia=TruncDay('fecha_creacion')
    ).values('dia').annotate(
        total=Count('id')
    ).order_by('dia')

    prediccion_labels = []
    prediccion_valores = []

    # 3.2. Solo si tenemos suficientes datos para entrenar (ej: más de 10 días)
    if len(tendencia_data_historica) > 10:
        
        # 3.3. Preparar datos con Pandas (fácil)
        df = pd.DataFrame(list(tendencia_data_historica))
        df['dia'] = pd.to_datetime(df['dia'])
        # Rellena días sin cotizaciones con 0 (clave para Time Series)
        df = df.set_index('dia').asfreq('D', fill_value=0) 
        
        try:
            # 3.4. Entrenar el modelo ARIMA (¡Esto es ML!)
            # (order=(1,1,1) es una configuración simple, no te compliques con esto)
            modelo = ARIMA(df['total'], order=(1, 1, 1))
            modelo_fit = modelo.fit()
            
            # 3.5. Predecir los próximos 7 días
            prediccion = modelo_fit.forecast(steps=7)
            
            # 3.6. Preparar datos de predicción para el gráfico
            ultimo_dia = df.index[-1]
            for i in range(7):
                dia_futuro = (ultimo_dia + timedelta(days=i+1)).strftime('%d-%b')
                prediccion_labels.append(dia_futuro)
                # Nos aseguramos que la predicción no sea negativa
                prediccion_valores.append(max(0, round(prediccion.iloc[i], 1))) 
                
        except Exception as e:
            # Si el modelo falla (pasa a veces con pocos datos), no hacemos nada
            print(f"Error al entrenar modelo ML: {e}")
            pass # Los arrays de predicción quedarán vacíos

    # 3.7. Preparar datos históricos (los últimos 30 días) para el gráfico de tendencia
    tendencia_reciente_data = tendencia_data_historica.filter(dia__gte=hace_30_dias)
    tendencia_labels = [item['dia'].strftime('%d-%b') for item in tendencia_reciente_data]
    tendencia_valores = [item['total'] for item in tendencia_reciente_data]
    
    # --- 4. Enviar todo al contexto ---
    context = {
        # KPIs
        'kpi_tasa_conversion': tasa_conversion,
        'kpi_total_cotizaciones': total_cotizaciones,
        'kpi_promedio_cot_dia': promedio_cot_dia,
        'kpi_aprobadas': aprobadas,
        
        # Gráfico Embudo (JSON)
        'embudo_labels': json.dumps(embudo_labels),
        'embudo_valores': json.dumps(embudo_valores),
        
        # Gráfico Tendencia Histórica (JSON)
        'tendencia_labels': json.dumps(tendencia_labels),
        'tendencia_valores': json.dumps(tendencia_valores),
        
        # Gráfico Productos (JSON)
        'productos_labels': json.dumps(productos_labels),
        'productos_valores': json.dumps(productos_valores),
        
        # ¡¡DATOS NUEVOS DE ML!! (JSON)
        'prediccion_labels': json.dumps(prediccion_labels),
        'prediccion_valores': json.dumps(prediccion_valores),
    }
    return render(request, "admin/reportes_graficos.html", context)


@login_required
@user_passes_test(is_admin)
def historial_cotizaciones_view(request):
    """
    NUEVA VISTA: Muestra el historial de TODAS las cotizaciones
    con filtros de fecha, estado y búsqueda.
    """
    # 1. Obtenemos todos los valores de los filtros del form
    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')

    # 2. Query base: Todas las cotizaciones
    queryset = ChatCotizacion.objects.select_related(
        'cliente', 
        'producto', 
        'admin_asignado'
    ).all()

    # 3. Aplicamos los filtros si existen
    if q:
        queryset = queryset.filter(
            Q(id__icontains=q) | 
            Q(cliente__username__icontains=q) |
            Q(producto__nombre__icontains=q)
        )
    
    if estado:
        queryset = queryset.filter(estado=estado)
    
    # ¡Aquí está el filtro de tiempo que pediste!
    if desde:
        queryset = queryset.filter(fecha_actualizacion__date__gte=desde)
        
    if hasta:
        queryset = queryset.filter(fecha_actualizacion__date__lte=hasta)

    # Ordenamos por la más reciente
    queryset = queryset.order_by('-fecha_actualizacion')
    
    # 4. Paginación
    paginator = Paginator(queryset, 25) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 5. Enviamos todo al template
    context = { 
        "cotizaciones": page_obj,  # Enviamos las cotizaciones paginadas
        "page_obj": page_obj,      # El Paginator también se usa para los enlaces
        "q": q,                    # Devolvemos los filtros para que se queden en los inputs
        "estado": estado,
        "desde": desde,
        "hasta": hasta
    }
    # Apuntamos a un NUEVO template que crearemos en el Paso 2
    return render(request, "admin/historial_cotizaciones.html", context)


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
# VISTAS DE CHATBOT (GENERAL)
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

        conversation, _ = ChatConversation.objects.get_or_create(session_id=session_id)
        if request.user.is_authenticated:
            conversation.user = request.user
            conversation.save()
        
        ChatMessage.objects.create(conversation=conversation, message=user_message, is_bot=False)

        history_messages = conversation.messages.order_by('-timestamp')[:6]
        history = [{'message': msg.message, 'is_bot': msg.is_bot} for msg in reversed(history_messages)]

        chatbot = ChatBotService() 
        bot_response = chatbot.get_ai_response(user_message, history)
        
        ChatMessage.objects.create(conversation=conversation, message=bot_response, is_bot=True)

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
        msgs = ChatMessage.objects.filter(conversation=conv).order_by('timestamp')
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


# ===========================
# VISTAS DE CLIENTE
# ===========================

@login_required
def client_dashboard(request):
    user = request.user

    # Productos del cliente
    productos_adquiridos = ProductoAdquirido.objects.filter(
        cliente=user
    ).select_related('producto')
    
    # Catálogo disponible
    productos_disponibles = Producto.objects.filter(
        activo=True
    ).select_related('categoria').prefetch_related('imagenes')

    # --- LÓGICA DEL FORMULARIO DE AJUSTES (perfil_form) ---
    if request.method == "POST":
        perfil_form = ClienteProfileForm(request.POST, instance=user)
        if perfil_form.is_valid():
            perfil_form.save()
            messages.success(request, "Tus datos se actualizaron correctamente.")
            return redirect("client_dashboard")  # recarga el panel
    else:
        perfil_form = ClienteProfileForm(instance=user)

    context = {
        "user": user,
        "productos_adquiridos": productos_adquiridos,
        "productos_disponibles": productos_disponibles,
        "perfil_form": perfil_form,
    }
    return render(request, "cliente/client_dashboard.html", context)


# ===========================
# VISTAS PARA CHAT DE COTIZACIÓN (CLIENTE Y API)
# ===========================

# VISTA 1: Iniciar el chat
@login_required
def iniciar_chat_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    chat, created = ChatCotizacion.objects.get_or_create(
        cliente=request.user,
        producto=producto,
        defaults={'admin_asignado': request.user.is_staff and request.user or None}
    )
    
    if created:
        MensajeCotizacion.objects.create(
            chat=chat,
            autor=User.objects.filter(is_superuser=True).first(), 
            es_bot=True,
            mensaje=f"¡Hola! Gracias por tu interés en el producto: {producto.nombre}. Soy tu asistente. Para ayudarte, ¿podrías indicarme tu nombre completo?"
        )
    
    return JsonResponse({'status': 'ok', 'chat_id': chat.id})


# VISTA 2: La página del chat (la que ve el usuario, en iframe)
@xframe_options_sameorigin 
@login_required
def chat_cotizacion_view(request, chat_id):
    chat = get_object_or_404(ChatCotizacion, id=chat_id)
    
    if not (request.user == chat.cliente or request.user.is_staff):
        messages.error(request, "No tienes permiso para ver este chat.")
        return redirect('client_dashboard')
        
    context = {
        'chat': chat
    }
    return render(request, 'chat/chat_detail.html', context)


# VISTA 3: La API para enviar y recibir mensajes (AJAX)
@login_required
def chat_api_view(request, chat_id):
    chat = get_object_or_404(ChatCotizacion, id=chat_id)
    
    if not (request.user == chat.cliente or request.user.is_staff):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    def msg_to_json(m, user):
        return {
            'id': m.id,
            'autor': m.autor.username,
            'mensaje': m.mensaje,
            'imagen': m.imagen.url if m.imagen else None,
            'es_bot': m.es_bot,
            'es_mio': m.autor == user,
            'timestamp': m.timestamp.isoformat()
        }

    if request.method == 'POST':
        data = json.loads(request.body)
        mensaje_texto = data.get('mensaje', '')
        
        if not mensaje_texto:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
            
        nuevo_mensaje = MensajeCotizacion.objects.create(
            chat=chat,
            autor=request.user,
            mensaje=mensaje_texto
        )
        
        mensajes_a_enviar = [msg_to_json(nuevo_mensaje, request.user)]
        
        if is_cliente(request.user):
            respuesta_bot = procesar_respuesta_bot(chat, mensaje_texto)
            
            if respuesta_bot:
                bot_user = User.objects.filter(is_superuser=True).first()
                if bot_user:
                    bot_msg = MensajeCotizacion.objects.create(
                        chat=chat,
                        autor=bot_user, 
                        es_bot=True,
                        mensaje=respuesta_bot
                    )
                    mensajes_a_enviar.append(msg_to_json(bot_msg, request.user))
        
        return JsonResponse({'status': 'ok', 'mensajes': mensajes_a_enviar})

    if request.method == 'GET':
        ultimo_timestamp_cliente = request.GET.get('ultimo_mensaje', None)
        
        if ultimo_timestamp_cliente:
            mensajes_nuevos = chat.mensajes.filter(
                timestamp__gt=ultimo_timestamp_cliente
            ).order_by('timestamp')
        else:
            mensajes_nuevos = chat.mensajes.all().order_by('timestamp')
        
        mensajes_json = [msg_to_json(m, request.user) for m in mensajes_nuevos]
        
        return JsonResponse({'mensajes': mensajes_json})


# VISTA 4: La lógica del "Bot asistente" (REPARADO: Lógica de pasos)
def procesar_respuesta_bot(chat, ultimo_mensaje_cliente):
    if chat.estado not in ['pendiente', 'en_proceso'] and chat.cliente_mensaje_dato is not None:
        return None 
    
    if chat.mensajes.filter(autor__is_staff=True, es_bot=False).exists():
        if chat.estado == 'pendiente':
             chat.estado = 'en_proceso'
             chat.save()
        return None

    if len(ultimo_mensaje_cliente) > 500:
        return "Tu mensaje es muy largo (máximo 500 caracteres). Por favor, sé más breve."
    if len(ultimo_mensaje_cliente) < 2:
        return "No entendí tu respuesta. Por favor, intenta de nuevo."

    # 1. Pide NOMBRE
    if chat.cliente_nombre_dato is None:
        if len(ultimo_mensaje_cliente) < 5 or not re.search(r'\s', ultimo_mensaje_cliente):
             return "Por favor, ingresa tu nombre y apellido completo."
        chat.cliente_nombre_dato = ultimo_mensaje_cliente
        chat.save()
        return f"¡Genial, {chat.cliente_nombre_dato}! Ahora, ¿cuál es tu correo electrónico?"

    # 2. Pide EMAIL
    if chat.cliente_email_dato is None:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", ultimo_mensaje_cliente):
            return "Ese no parece ser un correo válido. Por favor, ingresa un email (ej: tu@correo.com)."
        chat.cliente_email_dato = ultimo_mensaje_cliente
        chat.save()
        return "Perfecto. ¿Cuál es tu número de teléfono (con WhatsApp, si es posible)?"
    
    # 3. Pide TELÉFONO
    if chat.cliente_telefono_dato is None:
        if not re.search(r'(\d.*){8,}', ultimo_mensaje_cliente):
             return "Por favor, ingresa un número de teléfono válido (ej: +56 9 1234 5678)."
        chat.cliente_telefono_dato = ultimo_mensaje_cliente
        chat.save()
        return "¡Gracias! Dado que nuestra cobertura es nacional, por favor, indícame la **Región y Comuna** donde se realizará la instalación o el proyecto."
        
    # 4. Pide REGIÓN/COMUNA (Guarda en cliente_rut_dato)
    if chat.cliente_rut_dato is None: 
        if len(ultimo_mensaje_cliente) < 5:
             return "Necesitamos la Región y Comuna (ej: Valparaíso, Viña del Mar) para evaluar la logística."
        chat.cliente_rut_dato = ultimo_mensaje_cliente
        chat.save()
        return "¡Excelente! Finalmente, ¿podrías darme **más detalles de tu proyecto** (ej: tipo de techo, metros cuadrados, propósito de la cotización, etc.)?"
        
    # 5. Pide MENSAJE y se despide (Guarda en cliente_mensaje_dato)
    if chat.cliente_mensaje_dato is None:
        if len(ultimo_mensaje_cliente) < 10:
             return "Por favor, dame un poco más de detalle sobre tu proyecto para que podamos ayudarte mejor."
        chat.cliente_mensaje_dato = ultimo_mensaje_cliente
        
        chat.estado = 'en_proceso' 
        chat.save()
        return f"¡Muchas gracias! Tu solicitud está completa. Un administrador de SIEER (vendedor) revisará toda la información ({chat.cliente_rut_dato}) y se unirá a este chat muy pronto. (Estado: En Proceso)"

    return None

# VISTA 5: Lista de chats para el cliente 
@xframe_options_sameorigin
@login_required
def lista_chats_cotizacion_view(request):
    chats = ChatCotizacion.objects.filter(cliente=request.user).order_by('-fecha_actualizacion')
    context = {
        'lista_de_chats': chats
    }
    return render(request, 'cliente/lista_chats_cotizacion.html', context)