"""
Django settings for umg_rover project.
"""
import os
import sys
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-xv$)k=u*g6f$g5=i8b6d%$+g(ry3r=c20r4eop0e4c_6y$qn9q'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'usuarios',
    'usuarios.apps.UsuariosConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'umg_rover.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.views.get_user_context',  # AGREGAR ESTA LÍNEA
            ],
        },
    },
]

WSGI_APPLICATION = 'umg_rover.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'compilador25z19',
        'USER': 'usr_comp25z19_oper',
        'PASSWORD': '[qRnCTk$:W>r',
        'HOST': 'www.server.daossystem.pro',
        'PORT': '3301',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'es-gt'
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Definir explícitamente STATIC_ROOT para resolver el problema de las rutas
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Crear directorios necesarios si no existen
os.makedirs(os.path.join(MEDIA_ROOT, 'credenciales'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'avatars'), exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# Configuración del Rover
# Añadir esto al final de tu archivo settings.py

# IP del ESP8266 RC Car
# Esto se puede cambiar en la interfaz del editor o via el panel de administración
ROVER_IP = '192.168.1.89'  # IP predeterminada en modo AP

# Configuración para transpilación y ejecución
ROVER_SETTINGS = {
    'wheel_circumference': 20,  # Circunferencia de la rueda en cm
    'default_speed': 6,         # Velocidad predeterminada (0-9)
    'simulation_enabled': True  # Habilitar simulación
}
# Configuración de correo para Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'zddeveloper7@gmail.com'
EMAIL_HOST_PASSWORD = 'pdrz ffya asqh buzs' 
DEFAULT_FROM_EMAIL = 'UMG Basic Rover'

# Twilio para WhatsApp (opcional)
# Para usar WhatsApp necesitas una cuenta en Twilio (www.twilio.com)
# Después de crear la cuenta, activa el Sandbox de WhatsApp y obtén estas credenciales
TWILIO_ACCOUNT_SID = 'TU_ACCOUNT_SID'  # Reemplaza con tu SID real
TWILIO_AUTH_TOKEN = 'TU_AUTH_TOKEN'  # Reemplaza con tu token real
TWILIO_WHATSAPP_NUMBER = '+14155238886'  # Este es el número estándar de sandbox de Twilio

# Configuración de sesiones
SESSION_COOKIE_AGE = 7200  # 2 horas en segundos
SESSION_SAVE_EVERY_REQUEST = True
# Añadir al final de settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
# Timeouts para requests
REQUEST_TIMEOUT = 30  # segundos

# Para ngrok
NGROK_TIMEOUT = 0.5  # segundos por comando

# ===== CONFIGURACIÓN PARA RENDER =====

import os

# Secret Key para producción
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# Configuración de ALLOWED_HOSTS para Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# IMPORTANTE: Agregar dominios de Render
ALLOWED_HOSTS.extend([
    'umg-rover-project.onrender.com',
    '.onrender.com',
    'localhost',
    '127.0.0.1',
])

# Debug en False para producción
if 'RENDER' in os.environ:
    DEBUG = False
    # NO TOCAR LA BASE DE DATOS - SQLite sigue siendo default
    # MySQL está disponible como DATABASES['mysql'] para tus procedimientos
    
# Whitenoise para servir archivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configuración de archivos estáticos para producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de CORS para producción
CORS_ALLOWED_ORIGINS = [
    "https://*.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]