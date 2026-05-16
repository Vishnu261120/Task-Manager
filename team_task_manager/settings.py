from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allowed Hosts
raw_hosts = os.getenv(
    'ALLOWED_HOSTS',
    '127.0.0.1,localhost,.onrender.com'
)

ALLOWED_HOSTS = [
    h.strip() for h in raw_hosts.split(',')
    if h.strip()
]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'http://127.0.0.1:8000,http://localhost:8000'
    ).split(',')
    if o.strip()
]

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'manager',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'team_task_manager.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [BASE_DIR / 'templates'],

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

WSGI_APPLICATION = 'team_task_manager.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default PK
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication Redirects
LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = '/login/'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}