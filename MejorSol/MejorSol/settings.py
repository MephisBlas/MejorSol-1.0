from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta # <--- AÑADIDO: Necesario para la configuración de JWT

# Cargar variables de entorno (buscará el .env en la carpeta 'Mejorsol/')
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR apunta a 'Mejorsol/' (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================
# CONFIGURACIONES DE SEGURIDAD
# ===========================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-temporal-cambiar-en-produccion')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Configuraciones de seguridad para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ===========================
# CONFIGURACIÓN DE APLICACIONES
# ===========================

INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # === TAREA T-R.S2.5 (Erick): AÑADIR APPS DE API Y SEGURIDAD JWT ===
    'rest_framework',
    'rest_framework_simplejwt',
    
    # Local apps
    'myapp',
]

# ===========================
# CONFIGURACIÓN DE MIDDLEWARE
# ===========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===========================
# CONFIGURACIÓN DE URLS Y TEMPLATES
# ===========================

ROOT_URLCONF = 'MejorSol.urls' # (Asegúrate de que 'MejorSol' sea el nombre correcto de la carpeta de settings)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'myapp' / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'MejorSol.wsgi.application' # (Asegúrate de que 'MejorSol' sea el nombre correcto)

# ===========================
# CONFIGURACIÓN DE BASE DE DATOS
# ===========================

# === TAREA T-R.S2.2 (Isaí): MIGRACIÓN A MYSQL ===
# Esta configuración reemplaza SQLite y lee las credenciales del archivo .env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE_NAME', 'mejorsol_db_prod'), 
        'USER': os.getenv('MYSQL_DATABASE_USER', 'root'),             
        'PASSWORD': os.getenv('MYSQL_DATABASE_PASSWORD', ''),         
        'HOST': os.getenv('MYSQL_DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('MYSQL_DATABASE_PORT', '3308'), # <-- USA EL PUERTO QUE TE FUNCIONÓ (3308 o 3309)
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# ===========================
# VALIDACIÓN DE CONTRASEÑAS
# ===========================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===========================
# CONFIGURACIÓN INTERNACIONAL
# ===========================

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True
USE_L10N = True

# ===========================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ===========================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'myapp/static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===========================
# CONFIGURACIÓN DE AUTENTICACIÓN
# ===========================

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True

# === CONFIGURACIÓN DE AUTENTICACIÓN DE API CON JWT (SPRINT 1 - Erick) ===
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # Por defecto, todas las APIs requieren token
    ]
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # Duración del token de acceso
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),   # Duración del token para refrescar
    'AUTH_HEADER_TYPES': ('Bearer',),              # El tipo de token que se espera en la cabecera
}

# ===========================
# CONFIGURACIÓN DE CORREO
# ===========================

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@sieer.cl')

# ===========================
# CONFIGURACIONES ADICIONALES
# ===========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

APP_CONFIG = {
    'EMPRESA_NOMBRE': 'SIEER Chile',
    'EMPRESA_RUT': '76.123.456-7',
    'EMPRESA_DIRECCION': 'Av. Principal 123, Santiago, Chile',
    'EMPRESA_TELEFONO': '+56 2 1234 5678',
    'EMPRESA_EMAIL': 'contacto@sieer.cl',
    'IVA_PORCENTAJE': 19,
}