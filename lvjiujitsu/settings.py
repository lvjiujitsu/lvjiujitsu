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


# ── Ambiente ──────────────────────────────────────────────────────────────────
DJANGO_ENVIRONMENT = config("DJANGO_ENVIRONMENT", default="local").strip().lower()
if DJANGO_ENVIRONMENT not in {"local", "hg", "prod"}:
    raise ImproperlyConfigured(
        "DJANGO_ENVIRONMENT deve ser 'local', 'hg' ou 'prod'."
    )

DEBUG = config(
    "DJANGO_DEBUG",
    default=DJANGO_ENVIRONMENT == "local",
    cast=bool,
)
if DJANGO_ENVIRONMENT in {"hg", "prod"} and DEBUG:
    raise ImproperlyConfigured(
        "DJANGO_DEBUG deve ser False para os ambientes hg e prod."
    )


# ── Segurança ─────────────────────────────────────────────────────────────────
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

# Cookies seguros: False em DEBUG, True em produção — sobrescrevível via env
SESSION_COOKIE_SECURE = config("DJANGO_SESSION_COOKIE_SECURE", default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE    = config("DJANGO_CSRF_COOKIE_SECURE",    default=not DEBUG, cast=bool)
SESSION_COOKIE_SAMESITE = config("DJANGO_SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE    = config("DJANGO_CSRF_COOKIE_SAMESITE",    default="Lax")

# HSTS: 0 em DEBUG, 1 ano em produção — sobrescrevível via env
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

# Necessário para que Django enxergue HTTPS atrás do proxy do Render
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ── Admin / seeds ─────────────────────────────────────────────────────────────
ADMIN_SUPERUSER_USERNAME = config("ADMIN_SUPERUSER_USERNAME", default="")
ADMIN_SUPERUSER_EMAIL    = config("ADMIN_SUPERUSER_EMAIL",    default="")
ADMIN_SUPERUSER_PASSWORD = config("ADMIN_SUPERUSER_PASSWORD", default="")

SEED_INITIAL_TEACHER_PASSWORD        = config("SEED_INITIAL_TEACHER_PASSWORD",        default="")
SEED_INITIAL_ADMINISTRATIVE_PASSWORD = config("SEED_INITIAL_ADMINISTRATIVE_PASSWORD", default="")


# ── Stripe ────────────────────────────────────────────────────────────────────
STRIPE_PUBLIC_KEY      = config("STRIPE_PUBLIC_KEY",      default="")
STRIPE_SECRET_KEY      = config("STRIPE_SECRET_KEY",      default="")
STRIPE_WEBHOOK_SECRET  = config("STRIPE_WEBHOOK_SECRET",  default="")
STRIPE_PLAN_SYNC_ENABLED = config("STRIPE_PLAN_SYNC_ENABLED", default=False, cast=bool)


# ── Site ──────────────────────────────────────────────────────────────────────
SITE_BASE_URL = config("SITE_BASE_URL", default="http://127.0.0.1:8000")


# ── Asaas ─────────────────────────────────────────────────────────────────────
ASAAS_API_KEY            = config("ASAAS_API_KEY",            default="")
ASAAS_API_URL            = config("ASAAS_API_URL",            default="")
ASAAS_WEBHOOK_TOKEN      = config("ASAAS_WEBHOOK_TOKEN",      default="")
ASAAS_API_TIMEOUT_SECONDS   = config("ASAAS_API_TIMEOUT_SECONDS",   default=20,  cast=int)
ASAAS_USER_AGENT            = config("ASAAS_USER_AGENT",            default="lvjiujitsu-django/1.0")
ASAAS_PIX_DUE_DAYS          = config("ASAAS_PIX_DUE_DAYS",          default=1,   cast=int)
ASAAS_PIX_EXPIRATION_MINUTES = config("ASAAS_PIX_EXPIRATION_MINUTES", default=30, cast=int)


# ── Negócio ───────────────────────────────────────────────────────────────────
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


# ── Email ─────────────────────────────────────────────────────────────────────
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


# ── Application definition ────────────────────────────────────────────────────

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
    'system.context_processors.portal_navigation',
]

# Em DEBUG: APP_DIRS=True para hot-reload. Em produção: cached.Loader para não
# recompilar templates a cada request (win grande em servidor fraco).
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


# ── Database ──────────────────────────────────────────────────────────────────
# Local dev (DEBUG=1, DATABASE_URL vazio): SQLite
# Render HG (DEBUG=0, DATABASE_URL=supabase-hg): PostgreSQL HG
# Render PROD (DEBUG=0, DATABASE_URL=supabase-prod): PostgreSQL PROD
DATABASE_URL = config("DATABASE_URL", default="").strip()
if DJANGO_ENVIRONMENT in {"hg", "prod"} and not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL deve ser definido para os ambientes hg e prod."
    )

if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
    # Supabase free com Transaction Pooler usa PgBouncer em transaction mode.
    DATABASES['default']['CONN_MAX_AGE'] = config('DB_CONN_MAX_AGE', default=0, cast=int)
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ── Cache ─────────────────────────────────────────────────────────────────────
# LocMemCache: embutido no Django, zero dependência extra, ideal para free tier.
# Para produção com múltiplos workers cada processo tem seu próprio cache em memória
# — suficiente para template cache e small object cache neste cenário.
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

# ── Sessões ───────────────────────────────────────────────────────────────────
# cached_db: lê da cache em memória (rápido), grava no banco (persistente).
# Elimina o SELECT na tabela django_session a cada request autenticado.
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# ── Password validation ───────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ── Internacionalização ───────────────────────────────────────────────────────

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


# ── Static / Media ────────────────────────────────────────────────────────────

STATIC_URL    = config("DJANGO_STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT   = base_dir_path_setting("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")

MEDIA_URL  = config("DJANGO_MEDIA_URL",  default="/media/")
MEDIA_ROOT = base_dir_path_setting("DJANGO_MEDIA_ROOT", BASE_DIR / "media")

LOGIN_URL           = "system:login"
LOGIN_REDIRECT_URL  = "system:dashboard-redirect"
LOGOUT_REDIRECT_URL = "system:login"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEST_RUNNER = 'system.test_runner.PostgreSQLDiscoverRunner'


# ── WhiteNoise ────────────────────────────────────────────────────────────────
# CompressedManifestStaticFilesStorage: gera .gz e .br na build (collectstatic),
# serve direto sem recomprimir por request. Cache-busting via hash no nome do arquivo.
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
# 1 ano de cache nos assets — o hash no nome garante que mudanças invalidam o cache.
WHITENOISE_MAX_AGE = config('WHITENOISE_MAX_AGE', default=31536000 if not DEBUG else 0, cast=int)


# ── Logging ───────────────────────────────────────────────────────────────────
# Em produção: só WARNING+ para reduzir I/O. Em DEBUG: padrão Django.
if not DEBUG:
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
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
    }
