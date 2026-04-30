"""
Django settings for Stargazer.

Production-ready: reads config from environment variables,
serves React frontend as static files via WhiteNoise.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-only-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apod',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves static files in production without nginx/CDN.
    # The WHY: In dev, Django serves static files itself. In production,
    # that's slow. WhiteNoise compresses and caches static files in
    # memory, serving them directly from the WSGI layer. No nginx needed.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'stargazer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Look for templates in the React build output
        'DIRS': [BASE_DIR / 'frontend' / 'dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'stargazer.wsgi.application'

# Database
# The WHY behind dj-database-url: Railway/Render/Heroku all provide
# a DATABASE_URL environment variable. dj-database-url parses it into
# Django's DATABASES format. One env var replaces 5 settings.
# Falls back to local PostgreSQL for development.
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://stargazer:stargazer@localhost:5432/stargazer'
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
# The WHY: In production, Django collects all static files into STATIC_ROOT,
# then WhiteNoise serves them. STATICFILES_DIRS tells collectstatic where
# to find the React build output (frontend/dist/assets/).
STATIC_URL = '/assets/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'dist' / 'assets',
]

# WhiteNoise compression + caching (forever-cache for hashed filenames)
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
