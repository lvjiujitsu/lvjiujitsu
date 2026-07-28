import os
from pathlib import Path

from decouple import Config, RepositoryEnv, config as decouple_config
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def load_config():
    configured_env_file = os.environ.get("DJANGO_ENV_FILE", "").strip()
    if configured_env_file:
        env_path = Path(configured_env_file)
        if not env_path.is_absolute():
            env_path = BASE_DIR / env_path
        if not env_path.is_file():
            raise ImproperlyConfigured(
                f"DJANGO_ENV_FILE aponta para arquivo inexistente: {env_path}"
            )
        return Config(RepositoryEnv(str(env_path)))

    default_env_path = BASE_DIR / ".env"
    if default_env_path.is_file():
        return Config(RepositoryEnv(str(default_env_path)))

    return decouple_config


config = load_config()


def base_dir_path_setting(name, default):
    configured_path = Path(config(name, default=str(default)))
    if configured_path.is_absolute():
        return configured_path
    return BASE_DIR / configured_path


DJANGO_ENVIRONMENT = config("DJANGO_ENVIRONMENT", default="local").strip().lower()
REMOTE_ENVIRONMENTS = {"hg", "prod"}
if DJANGO_ENVIRONMENT not in {"local", *REMOTE_ENVIRONMENTS}:
    raise ImproperlyConfigured(
        "DJANGO_ENVIRONMENT deve ser 'local', 'hg' ou 'prod'."
    )

DEBUG = config(
    "DJANGO_DEBUG",
    default=DJANGO_ENVIRONMENT == "local",
    cast=bool,
)
if DJANGO_ENVIRONMENT in REMOTE_ENVIRONMENTS and DEBUG:
    raise ImproperlyConfigured(
        f"DJANGO_DEBUG deve ser False no ambiente {DJANGO_ENVIRONMENT}."
    )


SECRET_KEY = config("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY deve ser definido no ambiente.")
    SECRET_KEY = "django-insecure-dev-only-key-change-me"

ALLOWED_HOSTS = [
    h.strip()
    for h in config(
        "DJANGO_ALLOWED_HOSTS",
        default="127.0.0.1,localhost,localhost.,0.0.0.0",
    ).split(",")
    if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in config(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        default="http://127.0.0.1,http://localhost,https://127.0.0.1,https://localhost,https://*.ngrok-free.dev,https://*.ngrok.io",
    ).split(",")
    if o.strip()
]

SESSION_COOKIE_SECURE = config("DJANGO_SESSION_COOKIE_SECURE", default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE    = config("DJANGO_CSRF_COOKIE_SECURE",    default=not DEBUG, cast=bool)
SESSION_COOKIE_SAMESITE = config("DJANGO_SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE    = config("DJANGO_CSRF_COOKIE_SAMESITE",    default="Lax")

SECURE_HSTS_SECONDS = config(
    "DJANGO_SECURE_HSTS_SECONDS",
    default=0 if DEBUG else 31536000,
    cast=int,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=not DEBUG,
    cast=bool,
)
SECURE_HSTS_PRELOAD = config("DJANGO_SECURE_HSTS_PRELOAD", default=False, cast=bool)
SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"


ADMIN_SUPERUSER_USERNAME = config("ADMIN_SUPERUSER_USERNAME", default="")
ADMIN_SUPERUSER_EMAIL    = config("ADMIN_SUPERUSER_EMAIL",    default="")
ADMIN_SUPERUSER_PASSWORD = config("ADMIN_SUPERUSER_PASSWORD", default="")

SEED_INITIAL_TEACHER_PASSWORD        = config("SEED_INITIAL_TEACHER_PASSWORD",        default="")
SEED_INITIAL_ADMINISTRATIVE_PASSWORD = config("SEED_INITIAL_ADMINISTRATIVE_PASSWORD", default="")

SEED_TEST_PORTAL_PASSWORD = config("SEED_TEST_PORTAL_PASSWORD", default="")


STRIPE_PUBLIC_KEY      = config("STRIPE_PUBLIC_KEY",      default="")
STRIPE_SECRET_KEY      = config("STRIPE_SECRET_KEY",      default="")
STRIPE_WEBHOOK_SECRET  = config("STRIPE_WEBHOOK_SECRET",  default="")
STRIPE_PLAN_SYNC_ENABLED = config("STRIPE_PLAN_SYNC_ENABLED", default=False, cast=bool)


SITE_BASE_URL = config("SITE_BASE_URL", default="http://127.0.0.1:8000")


ASAAS_API_KEY            = config("ASAAS_API_KEY",            default="")
ASAAS_API_URL            = config("ASAAS_API_URL",            default="")
ASAAS_WEBHOOK_TOKEN      = config("ASAAS_WEBHOOK_TOKEN",      default="")
ASAAS_API_TIMEOUT_SECONDS   = config("ASAAS_API_TIMEOUT_SECONDS",   default=20,  cast=int)
ASAAS_USER_AGENT            = config("ASAAS_USER_AGENT",            default="lvjiujitsu-django/1.0")
ASAAS_PIX_DUE_DAYS          = config("ASAAS_PIX_DUE_DAYS",          default=1,   cast=int)
ASAAS_PIX_EXPIRATION_MINUTES = config("ASAAS_PIX_EXPIRATION_MINUTES", default=30, cast=int)


SITE_NAME             = config("SITE_NAME",             default="LV Jiu Jitsu")
SITE_NAME_UPPER       = config("SITE_NAME_UPPER",       default=SITE_NAME.upper())
PAYMENT_CURRENCY      = config("PAYMENT_CURRENCY",      default="brl").lower()
PAYMENT_CURRENCY_SYMBOL = config("PAYMENT_CURRENCY_SYMBOL", default="R$")
ASAAS_PIX_FIXED_FEE      = config("ASAAS_PIX_FIXED_FEE",      default="1.99")
ASAAS_CREDIT_PERCENT_FEE = config("ASAAS_CREDIT_PERCENT_FEE", default="0.0429")
ASAAS_CREDIT_FIXED_FEE   = config("ASAAS_CREDIT_FIXED_FEE",   default="0.49")
ASAAS_CARD_DUE_DAYS      = config("ASAAS_CARD_DUE_DAYS",      default=1, cast=int)
STRIPE_CREDIT_PERCENT_FEE = config("STRIPE_CREDIT_PERCENT_FEE", default="0.0399")
STRIPE_CREDIT_FIXED_FEE   = config("STRIPE_CREDIT_FIXED_FEE",   default="0.39")
CREDIT_CARD_FEE_PASS_THROUGH = config("CREDIT_CARD_FEE_PASS_THROUGH", default=True,  cast=bool)
PIX_FEE_PASS_THROUGH         = config("PIX_FEE_PASS_THROUGH",         default=True,  cast=bool)
PORTAL_PASSWORD_RESET_TOKEN_HOURS    = config("PORTAL_PASSWORD_RESET_TOKEN_HOURS",    default=2,  cast=int)
TRIAL_ACCESS_DEFAULT_CLASSES         = config("TRIAL_ACCESS_DEFAULT_CLASSES",         default=1,  cast=int)
BACKORDER_RESERVATION_DAYS           = config("BACKORDER_RESERVATION_DAYS",           default=7,  cast=int)
CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES = config("CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES", default=60, cast=int)
SPECIAL_CLASS_DEFAULT_TITLE             = config("SPECIAL_CLASS_DEFAULT_TITLE",             default="Aulão")
SPECIAL_CLASS_DEFAULT_DURATION_MINUTES  = config("SPECIAL_CLASS_DEFAULT_DURATION_MINUTES",  default=90, cast=int)
PAYROLL_REFUND_HOLD_DAYS = config("PAYROLL_REFUND_HOLD_DAYS", default=7, cast=int)
VETERAN_PLAN_TENURE_YEARS   = config("VETERAN_PLAN_TENURE_YEARS",   default=2,  cast=int)
VETERAN_PLAN_GAP_GRACE_DAYS = config("VETERAN_PLAN_GAP_GRACE_DAYS", default=60, cast=int)


EMAIL_BACKEND = config(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="nao-responda@lvjiujitsu.local",
)
EMAIL_HOST          = config("DJANGO_EMAIL_HOST",     default="smtp.gmail.com")
EMAIL_PORT          = config("DJANGO_EMAIL_PORT",     default=587, cast=int)
EMAIL_USE_TLS       = config("DJANGO_EMAIL_USE_TLS",  default=True, cast=bool)
EMAIL_HOST_USER     = config("DJANGO_EMAIL_HOST_USER",     default="")
EMAIL_HOST_PASSWORD = config("DJANGO_EMAIL_HOST_PASSWORD", default="")


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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'system.middleware.PortalSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lvjiujitsu.urls'

_CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
]

if DEBUG:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR / 'templates'],
            'APP_DIRS': True,
            'OPTIONS': {'context_processors': _CONTEXT_PROCESSORS},
        },
    ]
else:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR / 'templates'],
            'OPTIONS': {
                'context_processors': _CONTEXT_PROCESSORS,
                'loaders': [
                    (
                        'django.template.loaders.cached.Loader',
                        [
                            'django.template.loaders.filesystem.Loader',
                            'django.template.loaders.app_directories.Loader',
                        ],
                    )
                ],
            },
        },
    ]

WSGI_APPLICATION = 'lvjiujitsu.wsgi.application'


DATABASE_URL = config("DATABASE_URL", default="").strip()

SUPABASE_PROJECT_REF = config("SUPABASE_PROJECT_REF", default="").strip()
if DJANGO_ENVIRONMENT in REMOTE_ENVIRONMENTS and not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL deve ser definido para os ambientes hg e prod."
    )

if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
    DATABASES['default']['CONN_MAX_AGE'] = config('DB_CONN_MAX_AGE', default=0, cast=int)
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {'timeout': 20, 'transaction_mode': 'IMMEDIATE'},
        }
    }


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'lvjiujitsu-default',
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        },
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = config("DJANGO_LANGUAGE_CODE", default="pt-br")
TIME_ZONE     = config("DJANGO_TIME_ZONE",      default="America/Sao_Paulo")
USE_I18N = True
USE_TZ   = True

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
]
DATE_FORMAT     = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"


STATIC_URL    = config("DJANGO_STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT   = base_dir_path_setting("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

MEDIA_URL  = config("DJANGO_MEDIA_URL",  default="/media/")
MEDIA_ROOT = base_dir_path_setting("DJANGO_MEDIA_ROOT", BASE_DIR / "media")

LOGIN_URL           = "system:login"
LOGIN_REDIRECT_URL  = "system:dashboard-redirect"
LOGOUT_REDIRECT_URL = "system:login"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEST_RUNNER = "system.test_runner.ProjectDiscoverRunner"


STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if not DEBUG
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}
WHITENOISE_MAX_AGE = config('WHITENOISE_MAX_AGE', default=31536000 if not DEBUG else 0, cast=int)


_log_handler = 'null' if DEBUG else 'console'
LOG_LEVEL = config('DJANGO_LOG_LEVEL', default='WARNING').upper()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': [_log_handler],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': [_log_handler],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': [_log_handler],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': [_log_handler],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
