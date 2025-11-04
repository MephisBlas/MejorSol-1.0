from django.urls import include, path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

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
    
    # ===========================
    # URLS DE COTIZACIONES
    # ===========================
    path("cotizaciones/", views.cotizaciones_view, name="cotizaciones"),
    path("cotizaciones/nueva/", views.crear_cotizacion, name="crear_cotizacion"),
    path("cotizaciones/<int:cot_id>/", views.ver_cotizacion, name="ver_cotizacion"),
    path("cotizaciones/<int:cot_id>/editar/", views.editar_cotizacion, name="editar_cotizacion"),
    path("cotizaciones/<int:cot_id>/eliminar/", views.eliminar_cotizacion, name="eliminar_cotizacion"),
    
    # ===========================
    # URLS DE REPORTES
    # ===========================
    path('calculos/', views.calculos_estadisticas_view, name='calculos_estadisticas'),
    path('reportes/', views.reportes_graficos_view, name='reportes_graficos'),
    path('historial-ventas/', views.historial_ventas_view, name='historial_ventas'),
    
    # ===========================
    # URLS DE CUENTA
    # ===========================
    path('cuenta/', views.cuenta_view, name='cuenta'),
    path('configuracion/', views.configuracion, name='configuracion'),
    
    # ===========================
    # URLS DE API
    # ===========================
    path('send_message/', views.send_message, name='send_message'),
    path('conversation-history/<str:session_id>/', views.get_conversation_history, name='conversation_history'),
]