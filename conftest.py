"""
conftest.py — global pytest configuration for Enterprise DMS.

Run from /app inside the container:
    docker compose exec app pytest
"""
import importlib
from pathlib import Path

# Project root directory (where this conftest.py is located)
BASE_DIR = Path(__file__).resolve().parent


def _can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def pytest_configure(config):
    from django.conf import settings
    if settings.configured:
        return

    third_party = []
    candidates = [
        ('corsheaders',              'corsheaders'),
        ('nested_admin',             'nested_admin'),
        ('rest_framework',           'rest_framework'),
        ('rest_framework.authtoken', 'rest_framework'),
        ('django_filters',           'django_filters'),
        ('dal',                      'dal'),
        ('dal_select2',              'dal'),
    ]
    for django_app, python_module in candidates:
        if _can_import(python_module):
            third_party.append(django_app)

    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            },
            'enterprise_data': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            },
        },
        DATABASE_ROUTERS=['data.router.DataRouter'],
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            *third_party,
            'data',
            'users',
            'reports',
            'imports',
            'api',
        ],
        AUTH_USER_MODEL='users.CustomUser',
        SECRET_KEY='test-secret-key-only-for-pytest',
        DEBUG=True,
        ALLOWED_HOSTS=['*'],
        ROOT_URLCONF='EnterpriseApp.urls',
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            # Apuntar al directorio real de templates del proyecto
            'DIRS': [str(BASE_DIR / 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }],
        STATIC_URL='/static/',
        STATICFILES_DIRS=[str(BASE_DIR / 'static')],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        LANGUAGE_CODE='es-mx',
        TIME_ZONE='America/Mexico_City',
        USE_I18N=True,
        USE_TZ=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        LOGIN_URL='/login/',
    )
