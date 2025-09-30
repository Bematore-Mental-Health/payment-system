"""
Django settings for Bematore Payment System.

External payment processing system integrated with Firebase for authentication
and data synchronization. Designed to comply with Apple App Store guidelines.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
import pymysql

# Configure PyMySQL as MySQL client
pymysql.install_as_MySQLdb()


# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,payments.bematore.com').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'authentication',
    'payments',
    'callbacks',
    'firebase_sync',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'authentication.middleware.FirebaseAuthenticationMiddleware',
]

ROOT_URLCONF = 'bematore_payments.urls'

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

WSGI_APPLICATION = 'bematore_payments.wsgi.application'


# Database Configuration - MySQL for cPanel deployment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'bematore_payments'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Admin URL Configuration
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

# Firebase Configuration
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'bematore-public-app-d47e5')
FIREBASE_PRIVATE_KEY_PATH = os.getenv('FIREBASE_PRIVATE_KEY_PATH', 'firebase-adminsdk.json')

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Use service account key file
        cred = credentials.Certificate(FIREBASE_PRIVATE_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'projectId': FIREBASE_PROJECT_ID,
        })
    except Exception as e:
        print(f"Warning: Could not initialize Firebase: {e}")
        # Initialize without credentials for development
        firebase_admin.initialize_app()


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration for cPanel deployment
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'public_html', 'static')  # cPanel compatible path

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Add WhiteNoise for static file serving in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration for cPanel
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'public_html', 'media')  # cPanel compatible path


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS Configuration (for Flutter app)
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS', 
    'http://localhost:3000,https://bematore.com,https://app.bematore.com'
).split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'firebase-token',
]

# Security Configuration (Production-ready)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_PROXY_SSL_HEADER = tuple(os.getenv('SECURE_PROXY_SSL_HEADER', 'HTTP_X_FORWARDED_PROTO,https').split(',')) if os.getenv('SECURE_PROXY_SSL_HEADER') else None
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = os.getenv('SECURE_BROWSER_XSS_FILTER', 'True').lower() == 'true'
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

# Payment Configuration
PAYMENT_CONFIG = {
    # M-Pesa Configuration (reuse from Flutter app)
    'MPESA': {
        'CONSUMER_KEY': os.getenv('MPESA_CONSUMER_KEY'),
        'CONSUMER_SECRET': os.getenv('MPESA_CONSUMER_SECRET'),
        'PASS_KEY': os.getenv('MPESA_PASS_KEY'),
        'BUSINESS_SHORTCODE': os.getenv('MPESA_BUSINESS_SHORTCODE'),
        'ENVIRONMENT': os.getenv('MPESA_ENVIRONMENT', 'sandbox'),
        'CALLBACK_URL': os.getenv('MPESA_CALLBACK_URL', 'https://payments.bematore.com/api/v1/callbacks/mpesa/'),
    },
    
    # Flutterwave Configuration
    'FLUTTERWAVE': {
        'PUBLIC_KEY': os.getenv('FLUTTERWAVE_PUBLIC_KEY'),
        'SECRET_KEY': os.getenv('FLUTTERWAVE_SECRET_KEY'),
        'ENVIRONMENT': os.getenv('FLUTTERWAVE_ENVIRONMENT', 'test'),
        'WEBHOOK_SECRET': os.getenv('FLUTTERWAVE_WEBHOOK_SECRET'),
    },
    
    # PayPal Configuration
    'PAYPAL': {
        'CLIENT_ID': os.getenv('PAYPAL_CLIENT_ID'),
        'CLIENT_SECRET': os.getenv('PAYPAL_CLIENT_SECRET'),
        'ENVIRONMENT': os.getenv('PAYPAL_ENVIRONMENT', 'sandbox'),
    },
    
    # General Payment Settings
    'MINIMUM_AMOUNT': float(os.getenv('MINIMUM_PAYMENT_AMOUNT', '1.0')),
    'MAXIMUM_AMOUNT': float(os.getenv('MAXIMUM_PAYMENT_AMOUNT', '10000.0')),
    'TIMEOUT_SECONDS': int(os.getenv('PAYMENT_TIMEOUT_SECONDS', '300')),
    'DEFAULT_CURRENCY': os.getenv('DEFAULT_CURRENCY', 'USD'),  # Base currency for storage (consistent with Flutter)
    'DISPLAY_FALLBACK_CURRENCY': os.getenv('DISPLAY_FALLBACK_CURRENCY', 'KES'),  # Fallback for display
    
    # Currency Exchange Rates (should be updated regularly)
    'EXCHANGE_RATES': {
        'USD': 1.0,  # Base currency
        'KES': float(os.getenv('KES_EXCHANGE_RATE', '147.50')),  # USD to KES
        'EUR': float(os.getenv('EUR_EXCHANGE_RATE', '0.85')),
        'GBP': float(os.getenv('GBP_EXCHANGE_RATE', '0.73')),
    },
}

# Flutter App Configuration
FLUTTER_CONFIG = {
    'APP_URL': os.getenv('FLUTTER_APP_URL', 'https://app.bematore.com'),
    'SUCCESS_URL': os.getenv('FLUTTER_SUCCESS_URL', 'https://app.bematore.com/payment-success'),
    'FAILURE_URL': os.getenv('FLUTTER_FAILURE_URL', 'https://app.bematore.com/payment-failure'),
    'CANCEL_URL': os.getenv('FLUTTER_CANCEL_URL', 'https://app.bematore.com/payment-cancel'),
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'payment_system.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'payments': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': True},
        'callbacks': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': True},
        'firebase_sync': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': True},
    },
}
