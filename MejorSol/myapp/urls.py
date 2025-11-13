from django.urls import include, path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # ===========================
    # URLS PÚBLICAS
    # ===========================
    path('', views.index, name='index'),
    path('chatbot-demo/', views.chatbot_demo, name='chatbot_demo'),
    
    # ===========================
    # URLS DE AUTENTICACIÓN
    # ===========================
    path('registro/', views.registro, name='registro'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # ===========================
    # URLS DE PANELES
    # ===========================
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    
    # ===========================
    # URLS DE INVENTARIO (TODO INTEGRADO)
    # ===========================
    path('inventario/', views.control_inventario_view, name='control_inventario'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    
    # ==============================================================
    # URLS DE COTIZACIONES (ADMIN): CONFLICTOS RESUELTOS
    # La vista admin_lista_chats_cotizacion_view ahora usa el nombre 'cotizaciones'.
    # ==============================================================
    
    # 1. URL PRINCIPAL DE LISTADO (Nuevo listado de chats)
    path("cotizaciones/", views.admin_lista_chats_cotizacion_view, name="cotizaciones"),
    
    # 2. CHAT DE DETALLE
    path('cotizaciones/chat/<int:chat_id>/', views.admin_chat_cotizacion_view, name='admin_chat_cotizacion'), 
    
    # 3. CREAR (Corregido y consolidado el nombre)
    path("cotizaciones/crear/", views.crear_cotizacion, name="crear_cotizacion"),
    
    # 4. REDIRECCIONES ANTIGUAS (Siguen usando las vistas de redirección)
    # Estas vistas deben redirigir a admin_chat_cotizacion_view o eliminar_cotizacion
    path("cotizaciones/antigua/<int:cot_id>/", views.ver_cotizacion, name="ver_cotizacion"),
    path("cotizaciones/antigua/<int:cot_id>/editar/", views.editar_cotizacion, name="editar_cotizacion"),
    path("cotizaciones/antigua/<int:cot_id>/eliminar/", views.eliminar_cotizacion, name="eliminar_cotizacion"),
    
    # ===========================
    # URLS DE REPORTES
    # ===========================
    path('calculos/', views.calculos_estadisticas_view, name='calculos_estadisticas'),
    path('reportes/', views.reportes_graficos_view, name='reportes_graficos'),
    path('historial-cotizaciones/', views.historial_cotizaciones_view, name='historial_cotizaciones'),
    
    # ===========================
    # URLS DE CUENTA
    # ===========================
    path('cuenta/', views.cuenta_view, name='cuenta'),
    path('configuracion/', views.configuracion, name='configuracion'),
    
    # ===========================
    # URLS DE API (CHATBOT GENERAL)
    # ===========================
    path('send_message/', views.send_message, name='send_message'),
    path('conversation-history/<str:session_id>/', views.get_conversation_history, name='conversation_history'),

    # ===========================
    # URLS PARA CHAT DE COTIZACIÓN (FLUJO MODAL DEL CLIENTE)
    # ===========================
    path('mis-cotizaciones/', views.lista_chats_cotizacion_view, name='lista_chats_cotizacion'),
    path('iniciar-chat-cotizacion/<int:producto_id>/', views.iniciar_chat_view, name='iniciar_chat_cotizacion'),
    path('chat-cotizacion/<int:chat_id>/', views.chat_cotizacion_view, name='chat_cotizacion_view'),
    path('api/chat/<int:chat_id>/mensajes/', views.chat_api_view, name='chat_api_view'),
    path('cambiar-contraseña/', 
         auth_views.PasswordChangeView.as_view(
             template_name='cliente/cambiar_password.html',
             success_url='/ajustes-cuenta/'
         ),
         name='password_change'),
    path(
    'cambiar-contrasena/',
    auth_views.PasswordChangeView.as_view(
        template_name='cliente/cambiar_password.html',
        success_url=reverse_lazy('client_dashboard'),  # después de cambiar, vuelve al panel
    ),
    name='password_change'
),
    
]