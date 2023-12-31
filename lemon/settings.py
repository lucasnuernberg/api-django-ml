"""
Django settings for lemon project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
from os import path
from django.utils.translation import gettext_lazy as _
import os
from dotenv import load_dotenv
from os import getenv, path
from google.oauth2 import service_account

load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-%u@pbwrm+g%lmraqx$=nhlla2)11mqy4m_8mb#&wwl3*kx8xcj'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['web-production-76cb.up.railway.app', '127.0.0.1', 'localhost', 'https://lemon-hub-app.vercel.app']

AUTH_USER_MODEL = 'authentication.CustomUser'


# Application definition

INSTALLED_APPS = [
    #'daphne',
    'meli.apps.MeliConfig',
    'authentication.apps.AuthenticationConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'storages'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    #'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_WHITELIST = [
    'http://localhost:5173',
    'http://localhost:5174',
    'https://web-production-76cb.up.railway.app',
    'http://localhost:19006',
    'https://banana-hub-cp9243z63-donavanmarques.vercel.app',
    'https://lemon-hub-app.vercel.app'
]


CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


CSRF_TRUSTED_ORIGINS = [
    'https://localhost:5173',
    'https://localhost:5174',
    'https://web-production-76cb.up.railway.app',
    'http://localhost:19006',
    'https://banana-hub-cp9243z63-donavanmarques.vercel.app',
    'https://lemon-hub-app.vercel.app'
]


ROOT_URLCONF = 'lemon.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'lemon.wsgi.application'

REDIS_URL = getenv('REDIS_URL')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    }
}

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Configurações de worker do Celery (opcional)
CELERY_WORKER_CONCURRENCY = 4  # Defina o número de processos de trabalho (workers)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Ajuste o valor conforme necessário


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': getenv('NAME_DB'),
            'USER': getenv('USER_DB'),
            'PASSWORD': getenv('PASS_DB'),
            'HOST': getenv('HOST_DB'),
            'PORT': getenv('PORT_DB'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '100/minute',
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=6),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=6),
}

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'pt-br'

LANGUAGES = [
    ('pt-br', _('Portuguese')),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = getenv('EMAIL_PORT') 
    EMAIL_HOST_USER = getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = getenv('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = True

#Config Google Cloud
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

GS_BUCKET_NAME = getenv('GS_BUCKET_NAME')
GS_PROJECT_ID = getenv('GS_PROJECT_ID')
GS_CREDENTIALS_JSON = os.path.join(BASE_DIR, 'config', 'credentials.json')
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(GS_CREDENTIALS_JSON)


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_ROOT = path.join(BASE_DIR, 'staticfiles')

STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
