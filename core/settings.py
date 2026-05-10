from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_USER_MODEL = 'user.Utilisateur'

# SECURITY
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-7pn-i#t&r0i^x)i(9*7!_d_$vg)qk#91b0mn5%b!^px2=e6zs(')
DEBUG = int(os.environ.get('DEBUG', 1))
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# APPLICATIONS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps
    "corsheaders",
    'user.apps.UserConfig',
    'planning.apps.PlanningConfig',
    'pilotage.apps.PilotageConfig',
    'referentiel.apps.ReferentielConfig',
    'exploitation.apps.ExploitationConfig',
    'security.apps.SecurityConfig',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'rest_framework_simplejwt.token_blacklist',
]

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'corsheaders.middleware.CorsMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000',   
).split(',')

CORS_ALLOW_CREDENTIALS = True 

# URLS & TEMPLATES
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# # DATABASE DOCKER CONFIG

# DATABASES = {
#     'default': {
#         'ENGINE': os.environ.get('DJANGO_DATABASE_ENGINE', 'django.db.backends.mysql'),
#         'NAME': os.environ.get('DJANGO_DATABASE_NAME', 'mydb'),
#         'USER': os.environ.get('DJANGO_DATABASE_USER', 'root'),
#         'PASSWORD': os.environ.get('DJANGO_DATABASE_PASSWORD', 'P@ssw0rd'),
#         'HOST': os.environ.get('DJANGO_DATABASE_HOST', 'db'),
#         'PORT': os.environ.get('DJANGO_DATABASE_PORT', '3306'),
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             'charset': 'utf8mb4',
#         }
#     }
# }

# LOCAL DATABASE CONFIG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydb',
        'USER': 'root',
        'PASSWORD': 'P@ssw0rd',
        'HOST': '127.0.0.1',
        'PORT': '3307',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

# LDAP
LDAP_SERVER = os.environ.get('LDAP_SERVER', '10.250.90.8')
LDAP_DOMAIN = os.environ.get('LDAP_DOMAIN', 'camlight.cm')
LDAP_PORT = int(os.environ.get('LDAP_PORT', 389))

# EMAIL
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '')
EMAIL_PORT = os.environ.get('DJANGO_EMAIL_PORT', '')
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_PASSWORD', '')

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": SECRET_KEY,
    "ALGORITHM": "HS256"
}

# INTERNATIONALISATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# STATIC & MEDIA
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'