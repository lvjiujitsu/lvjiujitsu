import os
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from decouple import Config, RepositoryEmpty, RepositoryEnv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SHARED_ENV_DIR_VARIABLE = "LVJIUJITSU_SHARED_ENV_DIR"
DEFAULT_SHARED_ENV_DIR = r"W:\Meu Drive\Desenvolvimento\lvjiujitsu"
ENVIRONMENT_VARIABLE = "DJANGO_ENVIRONMENT"


def shared_env_dir():
    return Path(os.environ.get(SHARED_ENV_DIR_VARIABLE) or DEFAULT_SHARED_ENV_DIR)


def env_file_candidates():
    configured = os.environ.get("DJANGO_ENV_FILE", "").strip()
    if not configured:
        return [BASE_DIR / ".env", shared_env_dir() / ".env"]
    path = Path(configured)
    if path.is_absolute():
        return [path]
    return [BASE_DIR / path, shared_env_dir() / path]


def locate_env_file(name):
    for candidate in (BASE_DIR / name, shared_env_dir() / name):
        if candidate.is_file():
            return candidate
    return None


def load_config():
    candidates = env_file_candidates()
    for candidate in candidates:
        if candidate.is_file():
            return Config(RepositoryEnv(str(candidate)))
    if os.environ.get(ENVIRONMENT_VARIABLE, "").strip():
        return Config(RepositoryEmpty())
    looked = "; ".join(str(candidate) for candidate in candidates)
    raise ImproperlyConfigured(
        f"Nenhuma configuração encontrada. Sem {ENVIRONMENT_VARIABLE} no "
        "ambiente do processo, é obrigatório haver arquivo. Procurado em: "
        f"{looked}. Defina DJANGO_ENV_FILE, restaure o arquivo no repositório, "
        "confira se o diretório compartilhado está montado "
        f"({SHARED_ENV_DIR_VARIABLE} troca o caminho) ou cadastre as variáveis "
        "no painel da plataforma."
    )


config = load_config()


def base_dir_path_setting(name: str, default: Path) -> Path:
    configured_path = Path(config(name, default=str(default)))
    if configured_path.is_absolute():
        return configured_path
    return BASE_DIR / configured_path


def env_value_strip_outer_quotes(key: str, default: str = "") -> str:
    raw = config(key, default=default).strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1].strip()
    return raw


def parse_phone_numbers(raw_value: str) -> list[str]:
    numbers = []
    for part in raw_value.split(","):
        digits = "".join(character for character in part if character.isdigit())
        if digits:
            numbers.append(digits)
    return numbers


def parse_db_url(url: str) -> dict:
    parsed = dj_database_url.parse(
        url, conn_max_age=config("DB_CONN_MAX_AGE", default=0, cast=int)
    )
    if not parsed.get("OPTIONS"):
        parsed["OPTIONS"] = {}
    parsed["DISABLE_SERVER_SIDE_CURSORS"] = True
    parsed["CONN_HEALTH_CHECKS"] = True
    return parsed


DJANGO_ENVIRONMENT = config("DJANGO_ENVIRONMENT", default="local").strip().lower()
REMOTE_ENVIRONMENTS = {"hg", "prod"}
if DJANGO_ENVIRONMENT not in {"local", *REMOTE_ENVIRONMENTS}:
    raise ImproperlyConfigured(
        "DJANGO_ENVIRONMENT deve ser 'local', 'hg' ou 'prod'."
    )

DEBUG = config("DJANGO_DEBUG", default=DJANGO_ENVIRONMENT == "local", cast=bool)
if DJANGO_ENVIRONMENT in REMOTE_ENVIRONMENTS and DEBUG:
    raise ImproperlyConfigured(
        f"DJANGO_DEBUG deve ser False no ambiente {DJANGO_ENVIRONMENT}."
    )

SECRET_KEY = config("DJANGO_SECRET_KEY", default="").strip()
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY deve ser definido no ambiente.")
    SECRET_KEY = "django-insecure-dev-only-change-me"

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
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        default=(
            "http://127.0.0.1,http://localhost,https://127.0.0.1,https://localhost,"
            "https://*.ngrok-free.dev,https://*.ngrok.io"
        ),
    ).split(",")
    if origin.strip()
]
if render_hostname:
    render_origin = f"https://{render_hostname}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

SESSION_COOKIE_SECURE = config(
    "DJANGO_SESSION_COOKIE_SECURE", default=not DEBUG, cast=bool
)
CSRF_COOKIE_SECURE = config("DJANGO_CSRF_COOKIE_SECURE", default=not DEBUG, cast=bool)
SESSION_COOKIE_SAMESITE = config("DJANGO_SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE = config("DJANGO_CSRF_COOKIE_SAMESITE", default="Lax")

SECURE_HSTS_SECONDS = config(
    "DJANGO_SECURE_HSTS_SECONDS", default=0 if DEBUG else 31536000, cast=int
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=not DEBUG, cast=bool
)
SECURE_HSTS_PRELOAD = config("DJANGO_SECURE_HSTS_PRELOAD", default=False, cast=bool)
SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    "system.apps.SystemConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "system.middleware.PortalSessionMiddleware",  # BN - business rule
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lvjiujitsu.urls"

CONTEXT_PROCESSORS = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
]

TEMPLATE_LIBRARIES = {
}

if DEBUG:
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [BASE_DIR / "templates"],
            "APP_DIRS": True,
            "OPTIONS": {
                "libraries": TEMPLATE_LIBRARIES,
                "context_processors": CONTEXT_PROCESSORS,
            },
        },
    ]
else:
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [BASE_DIR / "templates"],
            "OPTIONS": {
                "libraries": TEMPLATE_LIBRARIES,
                "context_processors": CONTEXT_PROCESSORS,
                "loaders": [
                    (
                        "django.template.loaders.cached.Loader",
                        [
                            "django.template.loaders.filesystem.Loader",
                            "django.template.loaders.app_directories.Loader",
                        ],
                    )
                ],
            },
        },
    ]

WSGI_APPLICATION = "lvjiujitsu.wsgi.application"
ASGI_APPLICATION = "lvjiujitsu.asgi.application"
TEST_RUNNER = "system.test_runner.ProjectDiscoverRunner"

DATABASE_URL = config("DATABASE_URL", default="").strip()

SUPABASE_PROJECT_REF = config("SUPABASE_PROJECT_REF", default="").strip()
if DJANGO_ENVIRONMENT in REMOTE_ENVIRONMENTS and not DATABASE_URL:
    raise ImproperlyConfigured(
        f"DATABASE_URL deve ser definido no ambiente {DJANGO_ENVIRONMENT}."
    )

if DATABASE_URL:
    DATABASES = {"default": parse_db_url(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {"timeout": 20, "transaction_mode": "IMMEDIATE"},
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "lvjiujitsu-default",
        "TIMEOUT": config("CACHE_TIMEOUT", default=300, cast=int),
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

AUTH_USER_MODEL = "system.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "system:login"
LOGIN_REDIRECT_URL = "system:home"
LOGOUT_REDIRECT_URL = "system:login"

LANGUAGE_CODE = config("DJANGO_LANGUAGE_CODE", default="pt-br")
TIME_ZONE = config("DJANGO_TIME_ZONE", default="America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
]
DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"

STATIC_URL = config("DJANGO_STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = base_dir_path_setting("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

MEDIA_URL = config("DJANGO_MEDIA_URL", default="/media/")
MEDIA_ROOT = base_dir_path_setting("DJANGO_MEDIA_ROOT", BASE_DIR / "media")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

WHITENOISE_MAX_AGE = config(
    "WHITENOISE_MAX_AGE", default=0 if DEBUG else 31536000, cast=int
)

SITE_NAME = config("SITE_NAME", default="LV Jiu Jitsu")
SITE_NAME_UPPER = config("SITE_NAME_UPPER", default=SITE_NAME.upper())
SITE_BASE_URL = config("SITE_BASE_URL", default="http://127.0.0.1:8000").rstrip("/")

EMAIL_BACKEND = config(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config(
    "DJANGO_DEFAULT_FROM_EMAIL", default="nao-responda@lvjiujitsu.local"
)
EMAIL_HOST = config("DJANGO_EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("DJANGO_EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("DJANGO_EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("DJANGO_EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("DJANGO_EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = config("DJANGO_EMAIL_TIMEOUT", default=10, cast=int)

BREVO_API_KEY = config("BREVO_API_KEY", default="").strip()
if (
    DJANGO_ENVIRONMENT in REMOTE_ENVIRONMENTS
    and EMAIL_BACKEND.endswith("BrevoEmailBackend")
    and not BREVO_API_KEY
):
    raise ImproperlyConfigured(
        f"BREVO_API_KEY deve ser definida no ambiente {DJANGO_ENVIRONMENT} "
        "para o envio de e-mail."
    )

CLOUDINARY_URL = config("CLOUDINARY_URL", default="").strip()
if DJANGO_ENVIRONMENT in REMOTE_ENVIRONMENTS and not CLOUDINARY_URL:
    raise ImproperlyConfigured(
        f"CLOUDINARY_URL deve ser definida no ambiente {DJANGO_ENVIRONMENT} "
        "para o armazenamento de arquivo enviado."
    )
if CLOUDINARY_URL:
    parsed_cloudinary_url = urlparse(CLOUDINARY_URL)
    if (
        parsed_cloudinary_url.scheme != "cloudinary"
        or not parsed_cloudinary_url.username
        or not parsed_cloudinary_url.password
        or not parsed_cloudinary_url.hostname
    ):
        raise ImproperlyConfigured(
            "CLOUDINARY_URL inválida. Use cloudinary://API_KEY:API_SECRET@CLOUD_NAME."
        )
    os.environ.setdefault("CLOUDINARY_URL", CLOUDINARY_URL)

UPLOAD_RECEIPT_FOLDER = config(
    "UPLOAD_RECEIPT_FOLDER", default="lvjiujitsu/payment-receipts"
)
UPLOAD_RECEIPT_MAX_BYTES = config(
    "UPLOAD_RECEIPT_MAX_BYTES", default=10 * 1024 * 1024, cast=int
)
UPLOAD_RECEIPT_URL_TTL = config("UPLOAD_RECEIPT_URL_TTL", default=300, cast=int)
UPLOAD_RECEIPT_TIMEOUT = config("UPLOAD_RECEIPT_TIMEOUT", default=20, cast=int)

LOG_LEVEL = config("DJANGO_LOG_LEVEL", default="DEBUG" if DEBUG else "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "system": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

LIST_PAGE_SIZE = config("LIST_PAGE_SIZE", default=25, cast=int)
DATA_TRANSFER_CHUNK_SIZE = config("DATA_TRANSFER_CHUNK_SIZE", default=200, cast=int)

CEP_LOOKUP_BUDGET_SECONDS = config("CEP_LOOKUP_BUDGET_SECONDS", default=6, cast=float)
CEP_LOOKUP_ATTEMPT_TIMEOUT = config("CEP_LOOKUP_ATTEMPT_TIMEOUT", default=3, cast=float)

EVENT_YEAR = config("EVENT_YEAR", default=date.today().year, cast=int)
if EVENT_YEAR < 2020 or EVENT_YEAR > 2100:
    raise ImproperlyConfigured("EVENT_YEAR deve estar entre 2020 e 2100.")

PORTAL_PASSWORD_RESET_TOKEN_HOURS = config(
    "PORTAL_PASSWORD_RESET_TOKEN_HOURS", default=2, cast=int
)
PORTAL_MAX_FAILED_LOGIN_ATTEMPTS = config(
    "PORTAL_MAX_FAILED_LOGIN_ATTEMPTS", default=5, cast=int
)

PUBLIC_REGISTRATION_FALLBACK_EMAIL = config(
    "PUBLIC_REGISTRATION_FALLBACK_EMAIL",
    default="cadastro-publico-pendente@lvjiujitsu.internal",
).strip()
PUBLIC_REGISTRATION_WHATSAPP_NUMBERS = parse_phone_numbers(
    config("PUBLIC_REGISTRATION_WHATSAPP_NUMBERS", default="")
)

LEGACY_DB_HOST = config("LEGACY_DB_HOST", default="").strip()
LEGACY_DB_PORT = config("LEGACY_DB_PORT", default="3306").strip()
LEGACY_DB_NAME = config("LEGACY_DB_NAME", default="").strip()
LEGACY_DB_USER = config("LEGACY_DB_USER", default="").strip()
LEGACY_DB_PASSWORD = config("LEGACY_DB_PASSWORD", default="").strip()
LEGACY_SYSTEM_BASE_URL = config("LEGACY_SYSTEM_BASE_URL", default="").strip().rstrip("/")
LEGACY_IMPORT_BATCH_SIZE = config("LEGACY_IMPORT_BATCH_SIZE", default=50, cast=int)

ADMIN_SUPERUSER_USERNAME = config("ADMIN_SUPERUSER_USERNAME", default="admin")
ADMIN_SUPERUSER_EMAIL = config("ADMIN_SUPERUSER_EMAIL", default="")
ADMIN_SUPERUSER_PASSWORD = config("ADMIN_SUPERUSER_PASSWORD", default="")

SEED_USER_PASSWORD = config("SEED_USER_PASSWORD", default="")
SEED_SELLER_USERNAME = config("SEED_SELLER_USERNAME", default="vendedor")
SEED_INITIAL_TEACHER_PASSWORD = config("SEED_INITIAL_TEACHER_PASSWORD", default="")
SEED_INITIAL_ADMINISTRATIVE_PASSWORD = config(
    "SEED_INITIAL_ADMINISTRATIVE_PASSWORD", default=""
)
SEED_TEST_PORTAL_PASSWORD = config("SEED_TEST_PORTAL_PASSWORD", default="")
SEED_USERS_PASSWORDS = env_value_strip_outer_quotes("SEED_USERS_PASSWORDS", default="")
SEED_PARTNER_PASSWORDS = env_value_strip_outer_quotes(
    "SEED_PARTNER_PASSWORDS", default=""
)
SEED_TEST_CLIENT_PASSWORD = env_value_strip_outer_quotes(
    "SEED_TEST_CLIENT_PASSWORD", default=""
)

TRIAL_ACCESS_DEFAULT_CLASSES = config(
    "TRIAL_ACCESS_DEFAULT_CLASSES", default=1, cast=int
)
BACKORDER_RESERVATION_DAYS = config("BACKORDER_RESERVATION_DAYS", default=7, cast=int)
CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES = config(
    "CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES", default=60, cast=int
)
SPECIAL_CLASS_DEFAULT_TITLE = config("SPECIAL_CLASS_DEFAULT_TITLE", default="Aulão")
SPECIAL_CLASS_DEFAULT_DURATION_MINUTES = config(
    "SPECIAL_CLASS_DEFAULT_DURATION_MINUTES", default=90, cast=int
)
PAYROLL_REFUND_HOLD_DAYS = config("PAYROLL_REFUND_HOLD_DAYS", default=7, cast=int)
VETERAN_PLAN_TENURE_YEARS = config("VETERAN_PLAN_TENURE_YEARS", default=2, cast=int)
VETERAN_PLAN_GAP_GRACE_DAYS = config(
    "VETERAN_PLAN_GAP_GRACE_DAYS", default=60, cast=int
)


# ----------------------------------------------------------------------------
# BN - business rule: cobrança fora da plataforma. Este é o único produto que
# processa pagamento por gateway externo; acima desta linha está a base técnica
# do repositório. Registro em obsidian/projetos/lvjiujitsu/.
# ----------------------------------------------------------------------------

PAYMENT_CURRENCY = config("PAYMENT_CURRENCY", default="brl").lower()
PAYMENT_CURRENCY_SYMBOL = config("PAYMENT_CURRENCY_SYMBOL", default="R$")

CREDIT_CARD_FEE_PASS_THROUGH = config(
    "CREDIT_CARD_FEE_PASS_THROUGH", default=True, cast=bool
)
PIX_FEE_PASS_THROUGH = config("PIX_FEE_PASS_THROUGH", default=True, cast=bool)

STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PLAN_SYNC_ENABLED = config("STRIPE_PLAN_SYNC_ENABLED", default=False, cast=bool)
STRIPE_CREDIT_PERCENT_FEE = config("STRIPE_CREDIT_PERCENT_FEE", default="0.0399")
STRIPE_CREDIT_FIXED_FEE = config("STRIPE_CREDIT_FIXED_FEE", default="0.39")

ASAAS_API_KEY = config("ASAAS_API_KEY", default="")
ASAAS_API_URL = config("ASAAS_API_URL", default="")
ASAAS_WEBHOOK_TOKEN = config("ASAAS_WEBHOOK_TOKEN", default="")
ASAAS_API_TIMEOUT_SECONDS = config("ASAAS_API_TIMEOUT_SECONDS", default=20, cast=int)
ASAAS_USER_AGENT = config("ASAAS_USER_AGENT", default="lvjiujitsu-django/1.0")
ASAAS_PIX_DUE_DAYS = config("ASAAS_PIX_DUE_DAYS", default=1, cast=int)
ASAAS_PIX_EXPIRATION_MINUTES = config(
    "ASAAS_PIX_EXPIRATION_MINUTES", default=30, cast=int
)
ASAAS_PIX_FIXED_FEE = config("ASAAS_PIX_FIXED_FEE", default="1.99")
ASAAS_CREDIT_PERCENT_FEE = config("ASAAS_CREDIT_PERCENT_FEE", default="0.0429")
ASAAS_CREDIT_FIXED_FEE = config("ASAAS_CREDIT_FIXED_FEE", default="0.49")
ASAAS_CARD_DUE_DAYS = config("ASAAS_CARD_DUE_DAYS", default=1, cast=int)
