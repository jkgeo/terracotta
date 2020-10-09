"""
Django settings for tcdjango project.

Generated by 'django-admin startproject' using Django 2.2.15.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from typing import Mapping, Any, Tuple, NamedTuple, Dict, List, Optional

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

def get_env_variable(var_name):
    """ Get the environment variable or return exception. """
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the {} environment variable".format(var_name)
        raise ImproperlyConfigured(error_msg)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable("TC_DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

SITE_URL = 'http://localhost:8000'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # terracotta
    'server',

    # django-rest-framework
    'rest_framework',
    'django_filters',
    'drf_yasg',

    # django-storages
    'storages',

    # django-cors-headers
    'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

"""
Postgres example - (install psycopg2)
"""
# [USER, PASS, NAME, HOST, PORT]
# DATABASE_SETTINGS = json.loads(get_env_variable('TCDJANGO_DB_SETTINGS'))

# pg_user = DATABASE_SETTINGS[0]
# pg_pass = DATABASE_SETTINGS[1]
# db_name = DATABASE_SETTINGS[2]
# pg_host = DATABASE_SETTINGS[3]
# pg_port = DATABASE_SETTINGS[4]

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': db_name,
#         'USER': pg_user,
#         'PASSWORD': pg_pass,
#         'HOST': pg_host,
#         'PORT': pg_port,
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


"""
TCDjango file storage settings
"""

### USE AWS S3 to store Raster Files ###
USE_S3_RASTERS = False

### USE AWS S3 to store static assets (css, js, etc.) ###
USE_S3_STATIC = False

if USE_S3_RASTERS or USE_S3_STATIC:
    USE_S3 = True
else:
    USE_S3 = False

### AWS S3 Storage Settings ###
if USE_S3:
    AWS_ACCESS_KEY_ID = get_env_variable('AWS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = get_env_variable('AWS_KEY')
    AWS_STORAGE_BUCKET_NAME = get_env_variable('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400'
    }
    ### Settings for static files in S3 ###
    if USE_S3_STATIC:
        AWS_DEFAULT_ACL = 'public-read'
        AWS_LOCATION = 'static'
        STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
        STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    STATIC_URL = '/static/'
        
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_DIR = os.path.join(BASE_DIR, 'media')
MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'

"""
Terracotta Settings
"""
# DEFAULT_TILE_SIZE: Tuple[int, int] = (256, 256)
DEFAULT_TILE_SIZE: int = 256

REPROJECTION_METHOD: str = 'linear'

RESAMPLING_METHOD: str = 'average'

#: Size of raster file in-memory cache in bytes
RASTER_CACHE_SIZE: int = 1024 * 1024 * 490  # 490 MB

#: Compression level of raster file in-memory cache, from 0-9
RASTER_CACHE_COMPRESS_LEVEL: int = 9

#: Send performance traces to AWS X-Ray
XRAY_PROFILE: bool = False

#: Compression level of output PNGs, from 0-9
PNG_COMPRESS_LEVEL: int = 1

"""
CORS
"""
CORS_ALLOW_ALL_ORIGINS = False