import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Configurar Django para que funcione el script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MejorSol.settings')
django.setup()

# Importar modelos
from django.contrib.auth.models import User
from myapp.models import ChatCotizacion, Producto, Perfil, Categoria

print("--- 1. LIMPIANDO DATOS DE PRUEBA VIEJOS ---")
# Borramos usuarios y cotizaciones de prueba anteriores para evitar errores de duplicados
User.objects.filter(username__startswith="cli_ia_").delete()
ChatCotizacion.objects.filter(cliente_mensaje_dato="Dato autogenerado para prueba de ML").delete()

print("--- 2. PREPARANDO PRODUCTOS ---")
cat, _ = Categoria.objects.get_or_create(nombre="General Demo")
prod, _ = Producto.objects.get_or_create(
    sku="SKU-ML-TEST", 
    defaults={'nombre': 'Panel Solar IA', 'precio': 150000, 'stock': 999, 'categoria': cat}
)

print("--- 3. GENERANDO HISTORIAL (90 DÍAS) ---")
now = timezone.now()

for i in range(90, -1, -1):
    fecha_simulada = now - timedelta(days=i)
    
    # --- A) CREAR CLIENTES (Crecimiento simulado) ---
    # Creamos clientes aleatorios
    if i % 2 == 0 or random.random() > 0.6:
        uid = random.randint(10000, 99999)
        u_name = f"cli_ia_{i}_{uid}"
        
        if not User.objects.filter(username=u_name).exists():
            u = User.objects.create_user(username=u_name, email=f"{u_name}@test.com", password='123')
            # Forzar fecha de registro al pasado
            u.date_joined = fecha_simulada
            u.save()
            
            # CORRECCIÓN DEL ERROR: No creamos el perfil, lo buscamos y editamos
            # (Porque tu signal ya lo creó automáticamente)
            if hasattr(u, 'perfil'):
                u.perfil.tipo_usuario = 'cliente'
                u.perfil.save()

    # --- B) CREAR COTIZACIONES (Tendencia de ventas) ---
    # Fórmula matemática para simular crecimiento: más ventas cerca de hoy (i=0)
    factor_crecimiento = (90 - i) * 0.08 
    cantidad_ventas = int(random.randint(0, 1) + factor_crecimiento)
    
    # Seleccionar un cliente al azar
    cliente_random = User.objects.filter(perfil__tipo_usuario='cliente').order_by('?').first()
    
    if cliente_random:
        for _ in range(cantidad_ventas):
            cot = ChatCotizacion.objects.create(
                cliente=cliente_random,
                producto=prod,
                estado=random.choice(['aprobada', 'pendiente', 'en_proceso']),
                cliente_mensaje_dato="Dato autogenerado para prueba de ML"
            )
            # Hackear la fecha de creación
            cot.fecha_creacion = fecha_simulada
            cot.fecha_actualizacion = fecha_simulada
            cot.save()

    if i % 10 == 0:
        print(f"   -> Procesando día histórico -{i}...")

print("-------------------------------------------------------------")
print("¡ÉXITO! BASE DE DATOS POBLADA CORRECTAMENTE.")
print("Ahora tu Machine Learning tiene datos reales para graficar.")
print("-------------------------------------------------------------")