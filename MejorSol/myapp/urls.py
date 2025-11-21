from django.urls import include, path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView, chatbot_dialogflow

urlpatterns = [
    path('panel/clientes/', views.admin_lista_clientes_view, name='lista_clientes'),
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
    # path('accounts/', include('django.contrib.auth.urls')), # <--- COMENTA ESTO PARA EVITAR CONFLICTOS

    # ===========================
    # RECUPERACIÓN DE CONTRASEÑA (EXTERNA)
    # ===========================
    # 1. Solicitar correo
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), 
         name='password_reset'),

    # 2. Mensaje de envío exitoso
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), 
         name='password_reset_done'),

    # 3. Link que llega al correo (Ingresar nueva clave)
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), 
         name='password_reset_confirm'),

    # 4. Mensaje de éxito final
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), 
         name='password_reset_complete'),
    
    # ===========================
    # URLS DE PANELES
    # ===========================
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    
    # ===========================
    # URLS DE INVENTARIO 
    # ===========================
    path('inventario/', views.control_inventario_view, name='control_inventario'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    
    # ===========================
    # URLS DE COTIZACIONES (ADMIN)
    # ===========================
    path("cotizaciones/", views.admin_lista_chats_cotizacion_view, name="cotizaciones"),
    path('cotizaciones/chat/<int:chat_id>/', views.admin_chat_cotizacion_view, name='admin_chat_cotizacion'), 
    path("cotizaciones/crear/", views.crear_cotizacion, name="crear_cotizacion"),
    
    # Redirecciones antiguas
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
    # API — CHAT GENERAL
    # ===========================
    path('send_message/', views.send_message, name='send_message'),
    path('conversation-history/<str:session_id>/', views.get_conversation_history, name='conversation_history'),

    # ===========================
    # CHAT DE COTIZACIONES (CLIENTE)
    # ===========================
    path('mis-cotizaciones/', views.lista_chats_cotizacion_view, name='lista_chats_cotizacion'),
    path('iniciar-chat-cotizacion/<int:producto_id>/', views.iniciar_chat_view, name='iniciar_chat_cotizacion'),
    path('chat-cotizacion/<int:chat_id>/', views.chat_cotizacion_view, name='chat_cotizacion_view'),
    path('api/chat/<int:chat_id>/mensajes/', views.chat_api_view, name='chat_api_view'),
    path('api/cotizacion/<int:chat_id>/estado/', views.actualizar_estado_rapido, name='actualizar_estado_rapido'),
   
    # ===========================
    # CAMBIO DE CONTRASEÑA (INTERNA)
    # ===========================
    path(
        'cambiar-contrasena/',
        auth_views.PasswordChangeView.as_view(
            template_name='cliente/cambiar_password.html',
            success_url=reverse_lazy('client_dashboard'),
        ),
        name='password_change'
    ),
    path('crear-admin-secreto-k29qjE7bZpXv8fA/', views.crear_superusuario_secreto, name='crear_admin_secreto'),
    # ===========================
    # CHATBOT DIALOGFLOW (FINAL)
    # ===========================
    path('api/chatbot-dialogflow/', views.chatbot_dialogflow, name='chatbot_dialogflow'),
]