# verify_tables.py
import django
import os
import sys

project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MejorSol.settings')
django.setup()

from django.db import connection

# Tablas que deberían existir
tables_to_check = ['myapp_chatcotizacion', 'cotizaciones_formulario', 'myapp_mensajecotizacion']

try:
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in cursor.fetchall()]

    print("=== VERIFICACIÓN DE TABLAS CREADAS ===")
    for table in tables_to_check:
        if table in existing_tables:
            print(f"✅ {table} - EXISTE")
        else:
            print(f"❌ {table} - NO EXISTE")

except Exception as e:
    print(f"Error: {e}")