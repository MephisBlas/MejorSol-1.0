"""
URL configuration for MejorSol project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    path('productos/', views.productos, name='productos'),
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



]
