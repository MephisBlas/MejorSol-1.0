from django.contrib import admin
from django.urls import include, path
from myapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('registro/', views.registro, name='registro'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('send_message/', views.send_message, name='send_message'),
    path('chatbot-demo/', views.chatbot_demo, name='chatbot_demo'),
    path('conversation-history/<str:session_id>/', views.get_conversation_history, name='conversation_history'),
    path("cotizaciones/", views.cotizaciones_view, name="cotizaciones"),
    path("cotizaciones/nueva/", views.crear_cotizacion, name="crear_cotizacion"),
    path("cotizaciones/<int:cot_id>/", views.ver_cotizacion, name="ver_cotizacion"),
    path("cotizaciones/<int:cot_id>/editar/", views.editar_cotizacion, name="editar_cotizacion"),
    path("cotizaciones/<int:cot_id>/eliminar/", views.eliminar_cotizacion, name="eliminar_cotizacion"),
    path('calculos/', views.calculos_estadisticas_view, name='calculos_estadisticas'),
    path('inventario/', views.control_inventario_view, name='control_inventario'),
    path('reportes/', views.reportes_graficos_view, name='reportes_graficos'),
    path('historial/', views.historial_ventas_view, name='historial_ventas'),
    path('cuenta/', views.cuenta_view, name='cuenta'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('productos-list/', views.productos_list, name='productos_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/editar/<int:pk>/', views.producto_edit, name='producto_edit'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    path('productos/detalle/<int:producto_id>/', views.producto_detail, name='producto_detail'),




]
        