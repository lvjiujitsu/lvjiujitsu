from pathlib import Path

from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def base_dir_path_setting(name, default):
    configured_path = Path(config(name, default=str(default)))
    if configured_path.is_absolute():
        return configured_path
    return BASE_DIR / configured_path


DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

SECRET_KEY = config("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY deve ser definido no .env.")
    SECRET_KEY = "django-insecure-dev-only-key-change-me"

ALLOWED_HOSTS = [
    host.strip()
    for host in config(
        "DJANGO_ALLOWED_HOSTS",
        default="127.0.0.1,localhost,localhost.,0.0.0.0",
    ).split(",")
    if host.strip()
]
if DEBUG and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("*")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        default="http://127.0.0.1,http://localhost,https://127.0.0.1,https://localhost,https://*.ngrok-free.dev,https://*.ngrok.io",
    ).split(",")
    if origin.strip()
]

SECURE_HSTS_SECONDS = config("DJANGO_SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("DJANGO_SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("DJANGO_CSRF_COOKIE_SECURE", default=False, cast=bool)

ADMIN_SUPERUSER_USERNAME = config("ADMIN_SUPERUSER_USERNAME", default="")
ADMIN_SUPERUSER_EMAIL = config("ADMIN_SUPERUSER_EMAIL", default="")
ADMIN_SUPERUSER_PASSWORD = config("ADMIN_SUPERUSER_PASSWORD", default="")

STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PLAN_SYNC_ENABLED = config("STRIPE_PLAN_SYNC_ENABLED", default=False, cast=bool)

ASAAS_API_KEY = config("ASAAS_API_KEY", default="")
ASAAS_API_URL = config("ASAAS_API_URL", default="")
ASAAS_WEBHOOK_TOKEN = config("ASAAS_WEBHOOK_TOKEN", default="")
ASAAS_API_TIMEOUT_SECONDS = config("ASAAS_API_TIMEOUT_SECONDS", default=20, cast=int)
ASAAS_USER_AGENT = config("ASAAS_USER_AGENT", default="lvjiujitsu-django/1.0")
ASAAS_PIX_DUE_DAYS = config("ASAAS_PIX_DUE_DAYS", default=1, cast=int)
ASAAS_PIX_EXPIRATION_MINUTES = config("ASAAS_PIX_EXPIRATION_MINUTES", default=30, cast=int)

SITE_NAME = config("SITE_NAME", default="LV Jiu Jitsu")
SITE_NAME_UPPER = config("SITE_NAME_UPPER", default=SITE_NAME.upper())
PAYMENT_CURRENCY = config("PAYMENT_CURRENCY", default="brl").lower()
PAYMENT_CURRENCY_SYMBOL = config("PAYMENT_CURRENCY_SYMBOL", default="R$")
ASAAS_PIX_FIXED_FEE = config("ASAAS_PIX_FIXED_FEE", default="1.99")
STRIPE_CREDIT_PERCENT_FEE = config("STRIPE_CREDIT_PERCENT_FEE", default="0.0399")
STRIPE_CREDIT_FIXED_FEE = config("STRIPE_CREDIT_FIXED_FEE", default="0.39")
PORTAL_PASSWORD_RESET_TOKEN_HOURS = config(
    "PORTAL_PASSWORD_RESET_TOKEN_HOURS",
    default=2,
    cast=int,
)
TRIAL_ACCESS_DEFAULT_CLASSES = config(
    "TRIAL_ACCESS_DEFAULT_CLASSES",
    default=1,
    cast=int,
)
BACKORDER_RESERVATION_DAYS = config(
    "BACKORDER_RESERVATION_DAYS",
    default=7,
    cast=int,
)
CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES = config(
    "CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES",
    default=60,
    cast=int,
)
SPECIAL_CLASS_DEFAULT_TITLE = config("SPECIAL_CLASS_DEFAULT_TITLE", default="Aulão")
SPECIAL_CLASS_DEFAULT_DURATION_MINUTES = config(
    "SPECIAL_CLASS_DEFAULT_DURATION_MINUTES",
    default=90,
    cast=int,
)
SEED_TEST_PORTAL_PASSWORD = config("SEED_TEST_PORTAL_PASSWORD", default="123456")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'system',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'system.middleware.PortalSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lvjiujitsu.urls'

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
                'system.context_processors.portal_navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'lvjiujitsu.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = config("DJANGO_LANGUAGE_CODE", default="pt-br")

TIME_ZONE = config("DJANGO_TIME_ZONE", default="America/Sao_Paulo")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = config("DJANGO_STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = base_dir_path_setting("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")

# Media files (uploads de usuário)
MEDIA_URL = config("DJANGO_MEDIA_URL", default="/media/")
MEDIA_ROOT = base_dir_path_setting("DJANGO_MEDIA_ROOT", BASE_DIR / "media")

LOGIN_URL = "system:login"
LOGIN_REDIRECT_URL = "system:dashboard-redirect"
LOGOUT_REDIRECT_URL = "system:login"

EMAIL_BACKEND = config(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="nao-responda@lvjiujitsu.local",
)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
