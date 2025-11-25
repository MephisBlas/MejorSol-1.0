import csv
import re
import json
import uuid
import random
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum, Count, ProtectedError, Avg
from django.db.models.functions import TruncMonth, TruncDay
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction
from django.views.decorators.clickjacking import xframe_options_sameorigin

# --- Formularios ---
from .forms import (
    RegistroForm, ProfileForm, ProductoForm, 
    ProductoAdquiridoForm, ProductoImagenFormSet, ClienteProfileForm
)
# --- Modelos ---
from .models import (
    ChatConversation, ChatMessage, Producto, Categoria, 
    ProductoAdquirido, ProductoImagen, Cotizacion, ItemCotizacion,
    ChatCotizacion, MensajeCotizacion, Perfil
)
# --- Servicios ---
from .services import ChatBotService 
from .services import DialogflowService

# --- MACHINE LEARNING (Scikit-Learn) ---
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
# ---------------------------------------


# ===========================
# DECORADORES Y UTILIDADES
# ===========================

def is_admin(user):
    return user.is_staff or user.is_superuser

def is_admin_or_vendedor(user):
    """Verifica si el usuario es administrador, superusuario o vendedor (por perfil)."""
    if user.is_staff or user.is_superuser:
         return True
    return user.is_authenticated and hasattr(user, 'perfil') and (user.perfil.tipo_usuario in ['admin', 'vendedor', 'superuser'])

def is_cliente(user):
    """Verifica si el usuario es un cliente."""
    return user.is_authenticated and hasattr(user, 'perfil') and (user.perfil.tipo_usuario == 'cliente')


# ===========================
# VISTAS PÚBLICAS Y AUTENTICACIÓN
# ===========================

def index(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_panel')
        return redirect('client_dashboard')
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
    now = timezone.now()
    
    kpi_cotizaciones_mes = ChatCotizacion.objects.filter(
        fecha_creacion__year=now.year,
        fecha_creacion__month=now.month
    ).count()

    kpi_total_productos = Producto.objects.count()
    kpi_total_clientes = Perfil.objects.filter(tipo_usuario='cliente').count()
    stock_data = Producto.objects.aggregate(total_stock=Sum('stock'))
    kpi_stock_total = stock_data['total_stock'] or 0
    
    act_cotizaciones = ChatCotizacion.objects.select_related('cliente', 'producto').order_by('-fecha_creacion')[:3]
    act_productos = Producto.objects.select_related('categoria').order_by('-fecha_creacion')[:2]
    act_clientes = Perfil.objects.select_related('usuario').filter(tipo_usuario='cliente').order_by('-fecha_creacion')[:2]

    context = {
        'user': request.user,
        'kpi_cotizaciones_mes': kpi_cotizaciones_mes,
        'kpi_total_productos': kpi_total_productos,
        'kpi_total_clientes': kpi_total_clientes,
        'kpi_stock_total': kpi_stock_total,
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
    action = request.GET.get('action')
    producto_id = request.GET.get('producto_id')
    
    if action in ['crear', 'editar']:
        if action == 'editar' and producto_id:
            producto = get_object_or_404(Producto, pk=producto_id)
            titulo = f'Editar Producto - {producto.nombre}'
        else:
            producto = Producto()
            titulo = 'Nuevo Producto'
        
        if request.method == 'POST':
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
            'mostrar_formulario': True, 'form': form, 'formset': formset,
            'titulo': titulo, 'action': action,
        }
        return render(request, 'admin/control_inventario.html', context)
    
    if action == 'detalle' and producto_id:
        producto = get_object_or_404(Producto, pk=producto_id)
        context = {'mostrar_detalles': True, 'producto': producto}
        return render(request, 'admin/control_inventario.html', context)
    
    if action == 'movimiento' and producto_id:
        producto = get_object_or_404(Producto, pk=producto_id)
        context = {'mostrar_movimiento': True, 'producto': producto}
        return render(request, 'admin/control_inventario.html', context)
    
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
        productos = productos.filter(stock__lte=F('stock_minimo'), activo=True, stock__gt=0)

    productos = productos.order_by('-fecha_creacion')
    
    if request.GET.get('export') == 'csv':
        return export_inventario_csv(productos)
    
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.filter(activo=True)
    
    context = {
        'productos': page_obj, 'categorias': categorias, 'mostrar_lista': True,
    }
    return render(request, 'admin/control_inventario.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    nombre_producto = producto.nombre
    
    chat_count = ChatCotizacion.objects.filter(producto=producto).count()
    adquirido_count = ProductoAdquirido.objects.filter(producto=producto).count()

    if chat_count > 0 or adquirido_count > 0:
        try:
            producto.activo = False
            producto.save()
            messages.warning(request, f'El producto "{nombre_producto}" no se puede eliminar porque tiene relaciones activas. Marcado como "Inactivo".')
        except Exception as e:
            messages.error(request, f'Error al desactivar: {e}')
    else:
        try:
            producto.delete()
            messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
        except ProtectedError as e:
            messages.error(request, f'Error: No se pudo eliminar. Protegido por BD: {e}')
        except Exception as e:
            messages.error(request, f'Error inesperado: {e}')
            
    return redirect('control_inventario')


def export_inventario_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
    writer = csv.writer(response)
    writer.writerow(['SKU', 'Producto', 'Categoría', 'Stock', 'Stock Mínimo', 'Precio', 'Estado'])
    for producto in queryset:
        estado = 'OK'
        if producto.stock <= producto.stock_minimo: estado = 'BAJO STOCK'
        elif not producto.activo: estado = 'INACTIVO'
        writer.writerow([
            producto.sku, producto.nombre,
            producto.categoria.nombre if producto.categoria else '',
            producto.stock, producto.stock_minimo, producto.precio, estado
        ])
    return response


# ===========================
# VISTAS DE COTIZACIONES
# ===========================

@login_required
@user_passes_test(is_admin_or_vendedor, login_url='/client-dashboard/')
def admin_lista_chats_cotizacion_view(request):
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
    chat = get_object_or_404(ChatCotizacion, id=chat_id)
    chat_api_url = reverse('chat_api_view', kwargs={'chat_id': chat.id}) 
    context = {
        'chat': chat, 'is_admin_view': True,
        'chat_api_url': chat_api_url, 'chat_estados': ChatCotizacion.ESTADO_CHOICES 
    }
    return render(request, 'chat/chat_detail.html', context)


# ================================================================
# NUEVA FUNCIÓN: ACTUALIZAR ESTADO RÁPIDO (AJAX)
# ================================================================
@require_POST
@login_required
@user_passes_test(is_admin_or_vendedor)
def actualizar_estado_rapido(request, chat_id):
    try:
        chat = get_object_or_404(ChatCotizacion, id=chat_id)
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('nuevo_estado')
        except:
            nuevo_estado = request.POST.get('nuevo_estado')

        estados_validos = dict(ChatCotizacion.ESTADO_CHOICES).keys()
        
        if nuevo_estado in estados_validos:
            chat.estado = nuevo_estado
            chat.save()
            return JsonResponse({'status': 'ok', 'mensaje': f'Estado actualizado a {nuevo_estado}'})
        else:
            return JsonResponse({'status': 'error', 'mensaje': 'Estado no válido'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)


# --- Redirecciones Antiguas ---

@login_required
@user_passes_test(is_admin)
def cotizaciones_view(request):
    return redirect('admin_lista_chats_cotizacion')

@login_required
@user_passes_test(is_admin)
def crear_cotizacion(request):
    messages.info(request, "Función manual.")
    return render(request, "admin/crear_cotizacion.html")

@login_required
@user_passes_test(is_admin)
def ver_cotizacion(request, cot_id):
    return redirect('admin_chat_cotizacion', chat_id=cot_id)

@login_required
@user_passes_test(is_admin)
def editar_cotizacion(request, cot_id):
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
# VISTAS DE REPORTES Y ML
# ===========================

@login_required
@user_passes_test(is_admin)
def calculos_estadisticas_view(request):
    total_ventas = ProductoAdquirido.objects.aggregate(total=Sum('precio_adquisicion'))['total'] or 0
    total_clientes = ProductoAdquirido.objects.values('cliente').distinct().count()
    total_productos = Producto.objects.filter(activo=True).count()
    context = {
        'total_ventas': total_ventas, 'total_clientes': total_clientes,
        'total_productos': total_productos,
    }
    return render(request, 'admin/calculos_estadisticas.html', context)


@login_required
@user_passes_test(is_admin)
def reportes_graficos_view(request):
    """
    Vista BI con MACHINE LEARNING MEJORADO:
    - Predicción de Demanda (Cotizaciones) con modelo más robusto
    - Predicción de Crecimiento de Clientes
    - Manejo elegante de datos insuficientes
    - Métricas de error y validación
    """
    
    # 1. OBTENCIÓN DE DATOS (Últimos 120 días para mejor análisis)
    hace_120 = timezone.now() - timedelta(days=120)
    
    # Datos reales de la BD
    data_cotizaciones = list(ChatCotizacion.objects.filter(fecha_creacion__gte=hace_120)
                             .annotate(dia=TruncDay('fecha_creacion'))
                             .values('dia').annotate(total=Count('id')).order_by('dia'))
                             
    data_clientes = list(User.objects.filter(perfil__tipo_usuario='cliente', date_joined__gte=hace_120)
                         .annotate(dia=TruncDay('date_joined'))
                         .values('dia').annotate(nuevos=Count('id')).order_by('dia'))

    # --- MODO PROFESIONAL: Datos de demostración realistas ---
    usar_demo = len(data_cotizaciones) < 10  # Mayor exigencia para datos reales

    if usar_demo:
        data_cotizaciones = []
        data_clientes = []
        base_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        acum_clientes = 25  # Base más realista
        
        # Simulación más sofisticada con tendencia + estacionalidad
        for i in range(120, -1, -1):
            fecha = base_date - timedelta(days=i)
            dia_num = 120 - i
            
            # Cotizaciones con crecimiento + estacionalidad semanal
            tendencia = 3 + (dia_num * 0.12)  # Crecimiento más suave
            estacionalidad = 2 * np.sin(2 * np.pi * dia_num / 7)  # Patrón semanal
            ruido = random.randint(-2, 3)
            ventas = max(1, int(tendencia + estacionalidad + ruido))
            data_cotizaciones.append({'dia': fecha, 'total': ventas})
            
            # Clientes con crecimiento orgánico
            if dia_num % 3 == 0:  # Cada 3 días en promedio
                nuevos = random.randint(1, 3)
                acum_clientes += nuevos
            data_clientes.append({'dia': fecha, 'total_acumulado': acum_clientes})

    # Inicializar variables para el template
    pred_cot_l, pred_cot_v = [], []
    tendencia_l, tendencia_v = [], []
    cli_l, cli_v, kpi_proy_cli = [], [], 0
    metricas_calidad = {'cotizaciones': {}, 'clientes': {}}

    # ------------------------------------------------------------
    # 2. ML MEJORADO: PREDICCIÓN COTIZACIONES (Random Forest)
    # ------------------------------------------------------------
    df = pd.DataFrame(data_cotizaciones)
    if not df.empty and len(df) > 5:
        # FIX ZONA HORARIA
        if df['dia'].dt.tz is not None:
            df['dia'] = df['dia'].dt.tz_localize(None)
        
        df = df.set_index('dia').asfreq('D', fill_value=0).reset_index()
        
        # INGENIERÍA DE FEATURES MEJORADA
        df['fecha_num'] = df['dia'].map(datetime.toordinal)
        df['dia_semana'] = df['dia'].dt.dayofweek
        df['es_fin_semana'] = df['dia_semana'].isin([5, 6]).astype(int)
        df['mes'] = df['dia'].dt.month
        df['rolling_avg_7'] = df['total'].rolling(window=7, min_periods=1).mean()
        
        # Features para el modelo
        feature_cols = ['fecha_num', 'dia_semana', 'es_fin_semana', 'mes', 'rolling_avg_7']
        X = df[feature_cols].fillna(0)
        y = df['total']
        
        try:
            # USAR RANDOM FOREST PARA MEJOR PREDICCIÓN
            if len(df) > 10:
                # Split train/test para validación
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                # Calcular métricas de calidad
                y_pred_test = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred_test)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                
                metricas_calidad['cotizaciones'] = {
                    'mae': round(mae, 2),
                    'rmse': round(rmse, 2),
                    'confianza': max(0, 100 - (mae * 10))  # Métrica de confianza simple
                }
            else:
                model = RandomForestRegressor(n_estimators=50, random_state=42)
                model.fit(X, y)
                metricas_calidad['cotizaciones'] = {'mae': 'N/A', 'rmse': 'N/A', 'confianza': 85}
            
            # Predecir próximos 5 días
            last_date = df['dia'].iloc[-1]
            next_days = [last_date + timedelta(days=i) for i in range(1, 6)]
            
            for i, d in enumerate(next_days):
                # Preparar features para predicción futura
                fecha_num = d.toordinal()
                dia_semana = d.weekday()
                es_fin_semana = 1 if dia_semana in [5, 6] else 0
                mes = d.month
                rolling_avg = df['total'].tail(7).mean()
                
                features_futuro = [[fecha_num, dia_semana, es_fin_semana, mes, rolling_avg]]
                pred = model.predict(features_futuro)[0]
                
                pred_cot_l.append(d.strftime('%d-%b'))
                pred_cot_v.append(max(0, round(pred, 1)))
                
        except Exception as e:
            # Fallback a Linear Regression si hay error
            try:
                model_fallback = LinearRegression()
                model_fallback.fit(X[['fecha_num']], y)
                last_date = df['dia'].iloc[-1]
                next_days = [last_date + timedelta(days=i) for i in range(1, 4)]
                
                for i, d in enumerate(next_days):
                    pred = model_fallback.predict([[d.toordinal()]])[0]
                    pred_cot_l.append(d.strftime('%d-%b'))
                    pred_cot_v.append(max(0, round(pred, 1)))
            except:
                pass

        # Datos históricos para visualización (últimos 45 días)
        hace_45 = df['dia'].iloc[-1] - timedelta(days=45)
        df_recent = df[df['dia'] >= hace_45]
        tendencia_l = df_recent['dia'].dt.strftime('%d-%b').tolist()
        tendencia_v = df_recent['total'].tolist()

    # ------------------------------------------------------------
    # 3. ML: PREDICCIÓN CLIENTES (MEJORADO)
    # ------------------------------------------------------------
    df_c = pd.DataFrame(data_clientes)
    if not df_c.empty and len(df_c) > 5:
        if df_c['dia'].dt.tz is not None:
            df_c['dia'] = df_c['dia'].dt.tz_localize(None)
        
        if not usar_demo:
            df_c = df_c.set_index('dia').asfreq('D', fill_value=0).reset_index()
            df_c['total_acumulado'] = df_c['nuevos'].cumsum()
        
        df_c['fecha_num'] = df_c['dia'].map(datetime.toordinal)
        df_c['dia_semana'] = df_c['dia'].dt.dayofweek
        
        try:
            # Modelo para crecimiento de clientes
            X_cli = df_c[['fecha_num', 'dia_semana']]
            y_cli = df_c['total_acumulado']
            
            model_cli = RandomForestRegressor(n_estimators=50, random_state=42)
            model_cli.fit(X_cli, y_cli)
            
            # Predecir 7 días
            last_d = df_c['dia'].iloc[-1]
            next_d = [last_d + timedelta(days=i) for i in range(1, 8)]
            
            for i, d in enumerate(next_d):
                pred = model_cli.predict([[d.toordinal(), d.weekday()]])[0]
                cli_l.append(d.strftime('%d-%b'))
                cli_v.append(int(pred))
            
            current_total = df_c['total_acumulado'].iloc[-1]
            kpi_proy_cli = max(0, int(cli_v[-1] - current_total))
            
        except Exception as e:
            # Fallback
            try:
                model_cli_fallback = LinearRegression()
                model_cli_fallback.fit(df_c[['fecha_num']], df_c['total_acumulado'])
                last_d = df_c['dia'].iloc[-1]
                next_d = [last_d + timedelta(days=i) for i in range(1, 8)]
                
                for i, d in enumerate(next_d):
                    pred = model_cli_fallback.predict([[d.toordinal()]])[0]
                    cli_l.append(d.strftime('%d-%b'))
                    cli_v.append(int(pred))
                
                current_total = df_c['total_acumulado'].iloc[-1]
                kpi_proy_cli = max(0, int(cli_v[-1] - current_total))
            except:
                pass

    # 4. DATOS ESTÁTICOS / KPIs FINALES (MEJORADOS)
    if usar_demo:
        embudo_l = ['Aprobada', 'En Proceso', 'Pendiente', 'Rechazada']
        embudo_v = [42, 28, 15, 8]
        prod_l = ['Panel Solar 500W', 'Inversor Híbrido', 'Batería Litio', 'Kit Básico', 'Cableado Especial']
        prod_v = [65, 48, 35, 22, 18]
        
        kpi_total = sum(tendencia_v) if tendencia_v else 156
        kpi_tasa = 42.3
        kpi_prom = round(kpi_total / 45, 1) if kpi_total else 3.5
        kpi_aprob = int(kpi_total * 0.42)
        
        # Indicador de datos demo
        datos_reales = False
    else:
        total = ChatCotizacion.objects.count()
        aprob = ChatCotizacion.objects.filter(estado='aprobada').count()
        kpi_tasa = round((aprob/total*100), 1) if total else 0
        kpi_total = total
        kpi_prom = round(kpi_total / 45.0, 1) if kpi_total else 0
        kpi_aprob = aprob
        
        e_data = ChatCotizacion.objects.values('estado').annotate(t=Count('id'))
        embudo_l = [dict(ChatCotizacion.ESTADO_CHOICES).get(x['estado'], x['estado']) for x in e_data]
        embudo_v = [x['t'] for x in e_data]
        
        p_data = ChatCotizacion.objects.values('producto__nombre').annotate(t=Count('id')).order_by('-t')[:5]
        prod_l = [x['producto__nombre'] for x in p_data if x['producto__nombre']]
        prod_v = [x['t'] for x in p_data if x['producto__nombre']]
        
        # Si no hay suficientes productos, completar con datos genéricos
        if len(prod_l) < 3:
            prod_l.extend(['Producto Varios A', 'Producto Varios B', 'Producto Varios C'][:3-len(prod_l)])
            prod_v.extend([5, 3, 2][:3-len(prod_v)])
        
        datos_reales = True

    # Contexto final para el HTML
    context = {
        'kpi_tasa_conversion': kpi_tasa, 
        'kpi_total_cotizaciones': kpi_total,
        'kpi_promedio_cot_dia': kpi_prom, 
        'kpi_aprobadas': kpi_aprob,
        'kpi_proyeccion_clientes': kpi_proy_cli,
        
        'embudo_labels': json.dumps(embudo_l), 
        'embudo_valores': json.dumps(embudo_v),
        'tendencia_labels': json.dumps(tendencia_l), 
        'tendencia_valores': json.dumps(tendencia_v),
        'productos_labels': json.dumps(prod_l), 
        'productos_valores': json.dumps(prod_v),
        'prediccion_labels': json.dumps(pred_cot_l), 
        'prediccion_valores': json.dumps(pred_cot_v),
        'clientes_ml_labels': json.dumps(cli_l), 
        'clientes_ml_valores': json.dumps(cli_v),
        
        # Nuevos datos para mostrar calidad de predicciones
        'metricas_calidad': metricas_calidad,
        'datos_reales': datos_reales,
        'usar_demo': usar_demo,
        'total_dias_analizados': len(data_cotizaciones),
    }
    return render(request, "admin/reportes_graficos.html", context)


@login_required
@user_passes_test(is_admin)
def historial_cotizaciones_view(request):
    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')

    queryset = ChatCotizacion.objects.select_related('cliente', 'producto', 'admin_asignado').all()

    if q:
        queryset = queryset.filter(Q(id__icontains=q) | Q(cliente__username__icontains=q) | Q(producto__nombre__icontains=q))
    if estado:
        queryset = queryset.filter(estado=estado)
    if desde:
        queryset = queryset.filter(fecha_actualizacion__date__gte=desde)
    if hasta:
        queryset = queryset.filter(fecha_actualizacion__date__lte=hasta)

    queryset = queryset.order_by('-fecha_actualizacion')
    paginator = Paginator(queryset, 25) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = { 
        "cotizaciones": page_obj, "page_obj": page_obj,
        "q": q, "estado": estado, "desde": desde, "hasta": hasta
    }
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

    return render(request, "admin/cuenta.html", { "perfil_form": perfil_form, "pass_form": pass_form })


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

        return JsonResponse({ 'status': 'success', 'response': bot_response, 'session_id': session_id })
    except Exception as e:
        return JsonResponse({ 'status': 'error', 'response': 'Lo siento, ocurrió un error.', 'error': str(e) })


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
    productos_adquiridos = ProductoAdquirido.objects.filter(cliente=user).select_related('producto')
    productos_disponibles = Producto.objects.filter(activo=True).select_related('categoria').prefetch_related('imagenes')

    if request.method == "POST":
        perfil_form = ClienteProfileForm(request.POST, instance=user)
        if perfil_form.is_valid():
            perfil_form.save()
            messages.success(request, "Tus datos se actualizaron correctamente.")
            return redirect("client_dashboard")
    else:
        perfil_form = ClienteProfileForm(instance=user)

    context = {
        "user": user, "productos_adquiridos": productos_adquiridos,
        "productos_disponibles": productos_disponibles, "perfil_form": perfil_form,
    }
    return render(request, "cliente/client_dashboard.html", context)


# ===========================
# VISTAS PARA CHAT DE COTIZACIÓN (CLIENTE Y API)
# ===========================

@login_required
def iniciar_chat_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    chat, created = ChatCotizacion.objects.get_or_create(
        cliente=request.user, producto=producto,
        defaults={'admin_asignado': request.user.is_staff and request.user or None}
    )
    if created:
        nombre_usuario = request.user.first_name if request.user.first_name else request.user.username
        mensaje_bienvenida = (
            f"¡Hola {nombre_usuario}! Soy el asistente virtual de ventas para el producto "
            f"**{producto.nombre}**. Tu interés ha sido registrado. "
            f"Un administrador o vendedor se unirá a este chat en breve para ayudarte con tu cotización. "
            f"Por favor, espera un momento o describe tu solicitud mientras te atienden."
        )
        MensajeCotizacion.objects.create(
            chat=chat, autor=User.objects.filter(is_superuser=True).first(), 
            es_bot=True, mensaje=mensaje_bienvenida
        )
    return JsonResponse({'status': 'ok', 'chat_id': chat.id})


@xframe_options_sameorigin 
@login_required
def chat_cotizacion_view(request, chat_id):
    chat = get_object_or_404(ChatCotizacion, id=chat_id)
    if not (request.user == chat.cliente or request.user.is_staff):
        messages.error(request, "No tienes permiso para ver este chat.")
        return redirect('client_dashboard')
    context = { 'chat': chat }
    return render(request, 'chat/chat_detail.html', context)


@login_required
def chat_api_view(request, chat_id):
    chat = get_object_or_404(ChatCotizacion, id=chat_id)
    if not (request.user == chat.cliente or request.user.is_staff):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    def msg_to_json(m, user):
        return {
            'id': m.id, 'autor': m.autor.username, 'mensaje': m.mensaje,
            'imagen': m.imagen.url if m.imagen else None,
            'es_bot': m.es_bot, 'es_mio': m.autor == user,
            'timestamp': m.timestamp.isoformat()
        }

    if request.method == 'POST':
        data = json.loads(request.body)
        mensaje_texto = data.get('mensaje', '')
        if not mensaje_texto:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
            
        nuevo_mensaje = MensajeCotizacion.objects.create(
            chat=chat, autor=request.user, mensaje=mensaje_texto
        )
        mensajes_a_enviar = [msg_to_json(nuevo_mensaje, request.user)]
        
        if is_cliente(request.user):
            respuesta_bot = procesar_respuesta_bot(chat, mensaje_texto)
            if respuesta_bot:
                bot_user = User.objects.filter(is_superuser=True).first()
                if bot_user:
                    bot_msg = MensajeCotizacion.objects.create(
                        chat=chat, autor=bot_user, es_bot=True, mensaje=respuesta_bot
                    )
                    mensajes_a_enviar.append(msg_to_json(bot_msg, request.user))
        
        return JsonResponse({'status': 'ok', 'mensajes': mensajes_a_enviar})

    if request.method == 'GET':
        ultimo_timestamp_cliente = request.GET.get('ultimo_mensaje', None)
        if ultimo_timestamp_cliente:
            mensajes_nuevos = chat.mensajes.filter(timestamp__gt=ultimo_timestamp_cliente).order_by('timestamp')
        else:
            mensajes_nuevos = chat.mensajes.all().order_by('timestamp')
        return JsonResponse({'mensajes': [msg_to_json(m, request.user) for m in mensajes_nuevos]})


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
        if ultimo_mensaje_cliente.lower().strip() not in ['si', 'sí', 'no', 'ok']:
            return "No entendí tu respuesta. Por favor, intenta de nuevo."
    
    usuario_registrado = chat.cliente
    def is_confirmation(msg):
        return msg.lower().strip() in ['si', 'sí', 'ok', 'yes', 'correcto']
    def is_negation(msg):
        return msg.lower().strip() in ['no', 'negativo', 'cambiar', 'corregir']

    def manejar_confirmacion(dato_chat, dato_user_profile, siguiente_paso_msg, mensaje_confirmacion, mensaje_peticion_dato_nuevo):
        if dato_chat is None:
            if dato_user_profile and dato_user_profile.strip() not in ['','None']:
                return (mensaje_confirmacion.format(dato=dato_user_profile), 'CONFIRMAR')
            else:
                return (siguiente_paso_msg, 'PEDIR')
        if dato_chat.startswith('CONFIRMAR_'):
            if is_confirmation(ultimo_mensaje_cliente):
                tipo = dato_chat.split('_')[-1]
                if tipo == 'NOMBRE':
                    chat.cliente_nombre_dato = f"{usuario_registrado.first_name} {usuario_registrado.last_name}".strip()
                    if chat.cliente_nombre_dato == '': chat.cliente_nombre_dato = usuario_registrado.username
                elif tipo == 'EMAIL': chat.cliente_email_dato = usuario_registrado.email
                elif tipo == 'TELEFONO': chat.cliente_telefono_dato = getattr(usuario_registrado.perfil, 'telefono', 'NO_PROPORCIONADO')
                chat.save()
                return (siguiente_paso_msg, 'CONFIRMADO')
            elif is_negation(ultimo_mensaje_cliente):
                if dato_chat.endswith('NOMBRE'): chat.cliente_nombre_dato = None
                elif dato_chat.endswith('EMAIL'): chat.cliente_email_dato = None
                elif dato_chat.endswith('TELEFONO'): chat.cliente_telefono_dato = None
                chat.save()
                return (mensaje_peticion_dato_nuevo, 'PEDIR_NUEVO')
            else:
                if dato_chat.endswith('NOMBRE'): chat.cliente_nombre_dato = None
                elif dato_chat.endswith('EMAIL'): chat.cliente_email_dato = None
                elif dato_chat.endswith('TELEFONO'): chat.cliente_telefono_dato = None
                chat.save()
                return ('DATA_PROVIDED', 'PEDIR_NUEVO')
        return None, 'COMPLETADO'

    # 1. NOMBRE
    if chat.cliente_nombre_dato is None or chat.cliente_nombre_dato.startswith('CONFIRMAR_'):
        nombre_perfil = f"{usuario_registrado.first_name} {usuario_registrado.last_name}".strip()
        if not nombre_perfil or nombre_perfil == ' ': nombre_perfil = usuario_registrado.username
        
        resultado, estado = manejar_confirmacion(
            chat.cliente_nombre_dato, nombre_perfil, 
            "Genial. Ahora, ¿cuál es tu correo electrónico?",
            "Tu nombre registrado es **{}**. ¿Es correcto para esta cotización? (Sí/No)",
            "De acuerdo. Por favor, ingresa el nombre y apellido."
        )
        if estado == 'CONFIRMAR':
            chat.cliente_nombre_dato = 'CONFIRMAR_NOMBRE'
            chat.save()
            return resultado
        if estado == 'PEDIR' or (estado == 'PEDIR_NUEVO' and not is_confirmation(ultimo_mensaje_cliente) and not is_negation(ultimo_mensaje_cliente)):
             if len(ultimo_mensaje_cliente) < 5 or not re.search(r'\s', ultimo_mensaje_cliente):
                 return "Por favor, ingresa el nombre y apellido completo."
             chat.cliente_nombre_dato = ultimo_mensaje_cliente
             chat.save()
             return "¡Genial, {}! Ahora, ¿cuál es tu correo electrónico?".format(chat.cliente_nombre_dato)

    # 2. EMAIL
    if chat.cliente_email_dato is None or chat.cliente_email_dato.startswith('CONFIRMAR_'):
        email_perfil = usuario_registrado.email
        resultado, estado = manejar_confirmacion(
            chat.cliente_email_dato, email_perfil, 
            "Perfecto. ¿Cuál es tu número de teléfono?",
            "Tu correo registrado es **{}**. ¿Es correcto? (Sí/No)",
            "Por favor, ingresa el correo electrónico (ej: tu@correo.com)."
        )
        if estado == 'CONFIRMAR':
            chat.cliente_email_dato = 'CONFIRMAR_EMAIL'
            chat.save()
            return resultado
        if estado == 'PEDIR' or (estado == 'PEDIR_NUEVO' and not is_confirmation(ultimo_mensaje_cliente) and not is_negation(ultimo_mensaje_cliente)):
            if not re.match(r"[^@]+@[^@]+\.[^@]+", ultimo_mensaje_cliente):
                return "Correo no válido. Por favor, ingresa un email (ej: tu@correo.com)."
            chat.cliente_email_dato = ultimo_mensaje_cliente
            chat.save()
            return "Perfecto. ¿Cuál es tu número de teléfono?"

    # 3. TELEFONO
    if chat.cliente_telefono_dato is None or chat.cliente_telefono_dato.startswith('CONFIRMAR_'):
        telefono_perfil = getattr(usuario_registrado.perfil, 'telefono', '')
        resultado, estado = manejar_confirmacion(
            chat.cliente_telefono_dato, telefono_perfil, 
            "¡Gracias! Indícame la **Región y Comuna**.",
            "Tu teléfono registrado es **{}**. ¿Es correcto? (Sí/No)",
            "Por favor, ingresa el número de teléfono."
        )
        if estado == 'CONFIRMAR':
            chat.cliente_telefono_dato = 'CONFIRMAR_TELEFONO'
            chat.save()
            return resultado
        if estado == 'PEDIR' or (estado == 'PEDIR_NUEVO' and not is_confirmation(ultimo_mensaje_cliente) and not is_negation(ultimo_mensaje_cliente)):
             if not re.search(r'(\d.*){8,}', ultimo_mensaje_cliente):
                 return "Teléfono no válido (ej: +56 9 1234 5678)."
             chat.cliente_telefono_dato = ultimo_mensaje_cliente
             chat.save()
             return "¡Gracias! Indícame la **Región y Comuna**."

    # 4. REGION/COMUNA
    if chat.cliente_rut_dato is None: 
        if len(ultimo_mensaje_cliente) < 5:
             return "Necesitamos la Región y Comuna para evaluar logística."
        chat.cliente_rut_dato = ultimo_mensaje_cliente
        chat.save()
        return "¡Excelente! Finalmente, ¿podrías darme **más detalles de tu proyecto**?"
        
    # 5. MENSAJE
    if chat.cliente_mensaje_dato is None:
        if len(ultimo_mensaje_cliente) < 10:
             return "Por favor, dame un poco más de detalle sobre tu proyecto."
        chat.cliente_mensaje_dato = ultimo_mensaje_cliente
        chat.estado = 'en_proceso' 
        chat.save()
        return f"¡Muchas gracias! Tu solicitud está completa. Un vendedor revisará la información y te contactará pronto."

    return None

@xframe_options_sameorigin
@login_required
def lista_chats_cotizacion_view(request):
    chats = ChatCotizacion.objects.filter(cliente=request.user).order_by('-fecha_actualizacion')
    context = { 'lista_de_chats': chats }
    return render(request, 'cliente/lista_chats_cotizacion.html', context)

# Dialogflow
dialogflow_service = DialogflowService()

def chatbot_dialogflow(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    msg = request.POST.get("message")
    session_id = request.POST.get("session_id", "default-session")
    df_response = dialogflow_service.detect_intent(session_id, msg)
    return JsonResponse(df_response)

# ===========================
# VISTA LISTA CLIENTES (NUEVA)
# ===========================
@login_required
@user_passes_test(is_admin)
def admin_lista_clientes_view(request):
    clientes = User.objects.filter(perfil__tipo_usuario='cliente').select_related('perfil').order_by('-date_joined')
    context = { 'clientes': clientes }
    return render(request, 'admin/lista_clientes.html', context)

# ==========================================================
# HACK ADMIN
# ==========================================================
def crear_superusuario_secreto(request):
    return HttpResponse("Función deshabilitada.")