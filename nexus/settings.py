import os
from pathlib import Path
from datetime import timedelta
try:
    # python-dotenv may not be installed in every environment used to run tests.
    # Make loading optional to avoid hard failures during CI or minimal dev setups.
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Use an environment-provided secret in all non-local environments.
# Keep the fallback intentionally short and non-sensitive so scanners don't
# flag it as a leaked credential. In production, always set DJANGO_SECRET_KEY
# to a secure, random 50+ character string via environment/secret manager.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-placeholder-key')

DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'catalog',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nexus.urls'

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

WSGI_APPLICATION = 'nexus.wsgi.application'

# Database
DATABASES = {}
if os.getenv('POSTGRES_HOST'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('POSTGRES_DB', 'nexus'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization / Localization
LANGUAGE_CODE = 'en'

# available languages for the site (English + Spanish sample)
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Use WhiteNoise to serve static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media settings for uploaded product images. Requires Pillow in the environment.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Optional S3 storage configuration (django-storages). To enable, set USE_S3=1 and provide
# AWS_S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_REGION_NAME in env.
# Add the following packages to production requirements: boto3, django-storages
USE_S3 = os.getenv('USE_S3', '0') == '1'
if USE_S3:
    # Prefer the new STORAGES setting on supported Django versions; fall back to DEFAULT_FILE_STORAGE
    storage_backend = os.getenv('AWS_STORAGE_BACKEND', 'storages.backends.s3boto3.S3Boto3Storage')
    try:
        # Use STORAGES on Django 4.3+ to avoid DEFAULT_FILE_STORAGE deprecation
        import django
        if getattr(django, 'VERSION', (0,)) >= (4, 3):
            STORAGES = {
                'default': {
                    'BACKEND': storage_backend,
                }
            }
        else:
            # older Django versions still expect DEFAULT_FILE_STORAGE
            DEFAULT_FILE_STORAGE = storage_backend
    except Exception:
        # If django isn't importable for some reason, fall back to the older setting to remain functional
        DEFAULT_FILE_STORAGE = storage_backend

    AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME') or os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_STORAGE_BUCKET_NAME = AWS_S3_BUCKET_NAME
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', None)
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', None)
    # Ensure we don't accidentally leave files publicly writable by default
    AWS_DEFAULT_ACL = None
    # Recommended: Use signature v4
    AWS_S3_SIGNATURE_VERSION = os.getenv('AWS_S3_SIGNATURE_VERSION', 's3v4')
    # Don't add querystring auth to stored urls (use presigned if needed)
    AWS_QUERYSTRING_AUTH = False
    # Cache control for public objects — set a sensible default, override via field-level args if needed
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': os.getenv('AWS_S3_CACHE_CONTROL', 'max-age=86400, public'),
    }
    # Use custom domain if provided (CloudFront recommended)
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN') or os.getenv('AWS_CLOUDFRONT_DOMAIN')
    # Optional presigned URL expiry (seconds)
    AWS_QUERYSTRING_EXPIRE = int(os.getenv('AWS_QUERYSTRING_EXPIRE', '3600'))
    # Update MEDIA_URL to point to the S3 location or CloudFront.
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN or AWS_S3_BUCKET_NAME}.s3.amazonaws.com/'

    # Security note: when deploying, use an IAM role with least privileges (see README for a policy example)
    # Example policy for S3 access:
    # {
    #     "Version": "2012-10-17",
    #     "Statement": [
    #         {
    #             "Effect": "Allow",
    #             "Action": [
    #                 "s3:ListBucket"
    #             ],
    #             "Resource": "arn:aws:s3:::your-bucket-name"
    #         },
    #         {
    #             "Effect": "Allow",
    #             "Action": [
    #                 "s3:GetObject",
    #                 "s3:PutObject",
    #                 "s3:DeleteObject"
    #             ],
    #             "Resource": "arn:aws:s3:::your-bucket-name/*"
    #         }
    #     ]
    # }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    # Throttling: apply anonymous and user throttles by default and allow scoped throttles
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/day',
        'user': '2000/day',
        # scoped key for product endpoints
        'products': '60/min',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', '7'))),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Project Nexus API',
    'DESCRIPTION': 'E-Commerce Backend APIs',
    'VERSION': '0.1.0',
}

# Expose JWT bearer auth in the OpenAPI schema so Swagger UI can send tokens
SPECTACULAR_SETTINGS.setdefault('COMPONENTS', {})
SPECTACULAR_SETTINGS['COMPONENTS'].setdefault('securitySchemes', {})
SPECTACULAR_SETTINGS['COMPONENTS']['securitySchemes']['jwtAuth'] = {
    'type': 'http',
    'scheme': 'bearer',
    'bearerFormat': 'JWT',
}
# Use the same key name in the global security requirement so the schema is
# consistent and Swagger UI only needs a single scheme name to present the
# Authorize control.
SPECTACULAR_SETTINGS.setdefault('SECURITY', [{'jwtAuth': []}])

# Caching configuration: use local memory cache by default, or Redis when USE_REDIS=1
USE_REDIS = os.getenv('USE_REDIS', '0') == '1'
CACHE_TTL = int(os.getenv('CACHE_TTL', '60'))  # default cache TTL in seconds for view caching
if USE_REDIS:
    # django-redis backend
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Email settings: use console backend in development unless overridden
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
