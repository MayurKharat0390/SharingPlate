import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'donations',
    'users',
    'crispy_forms',
    'crispy_bootstrap5',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'uhv_donation.urls'

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

LOGOUT_REDIRECT_URL = 'home'  # Add this line - redirect to home after logout

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'uhv.donation.platform@gmail.com'  # Your platform email
EMAIL_HOST_PASSWORD = 'pccoe@123'  # Google App Password
DEFAULT_FROM_EMAIL = 'noreply@uhvsharehub.com'
SERVER_EMAIL = 'noreply@uhvsharehub.com'

# Site information
SITE_URL = 'http://127.0.0.1:8000'  # Change in production
SITE_NAME = 'UHV ShareHub'

# Enable email notifications
ENABLE_EMAIL_NOTIFICATIONS = True

# Email addresses for different purposes
EMAIL_CONFIG = {
    'NOREPLY': 'noreply@uhvsharehub.com',
    'SUPPORT': 'support@uhvsharehub.com',
    'NOTIFICATIONS': 'notifications@uhvsharehub.com',
}
DEBUG = False
ALLOWED_HOSTS = ['SharingPlate.pythonanywhere.com']
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'