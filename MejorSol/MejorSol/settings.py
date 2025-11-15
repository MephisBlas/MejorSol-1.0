from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================
# CONFIGURACIONES DE SEGURIDAD
# ===========================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-temporal-cambiar-en-produccion')
# Importante: En Render DEBUG suele ser False, asegúrate de tener las variables configuradas
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Permitimos el host de Render (y todos para facilitar la demo)
ALLOWED_HOSTS = ['*']

# Configuraciones de seguridad para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Fix para que HTTPS funcione bien detrás del proxy de Render
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
    'django.contrib.staticfiles', # Necesario para whitenoise
    'django.contrib.humanize',
    
    # === TAREA T-R.S2.5 (Erick): AÑADIR APPS DE API Y SEGURIDAD JWT ===
    'rest_framework',
    'rest_framework_simplejwt',
    
    # Local apps
    'myapp',
]

# ===========================
# CONFIGURACIÓN DE MIDDLEWARE (¡CORREGIDO!)
# ===========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ------------------------------------------------------------------------
    # [CORRECCIÓN CRÍTICA] WhiteNoise debe ir AQUÍ, justo después de Security
    # ------------------------------------------------------------------------
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    
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

ROOT_URLCONF = 'MejorSol.urls' 

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

WSGI_APPLICATION = 'MejorSol.wsgi.application'

# ===========================
# CONFIGURACIÓN DE BASE DE DATOS
# ===========================

# === TAREA T-R.S2.2 (Isaí): MIGRACIÓN A MYSQL ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '3306',
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
# ARCHIVOS ESTÁTICOS Y MEDIA (¡AJUSTADO PARA RENDER!)
# ===========================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'myapp/static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  

# [AJUSTE DE SEGURIDAD] Usamos 'CompressedStaticFilesStorage' en lugar de 'Manifest...'
# Esto evita que el deploy falle si falta una imagen referenciada en el CSS.
# Es más seguro para entregas rápidas.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'  

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
        'rest_framework.permissions.IsAuthenticated', 
    ]
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), 
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),   
    'AUTH_HEADER_TYPES': ('Bearer',),              
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