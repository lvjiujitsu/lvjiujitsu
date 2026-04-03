import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

raw_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [host.strip() for host in raw_allowed_hosts.split(",") if host.strip()]
USE_SECURE_COOKIES = os.getenv("DJANGO_SECURE_COOKIES", "false").lower() == "true"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "allauth",
    "allauth.account",
    "system.apps.SystemConfig",
]

DJSTRIPE_ENABLED = os.getenv("DJSTRIPE_ENABLED", "false").lower() == "true"
DJSTRIPE_MIRROR_STRICT = os.getenv("DJSTRIPE_MIRROR_STRICT", "false").lower() == "true"
if DJSTRIPE_ENABLED:
    INSTALLED_APPS.append("djstripe")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "system.middleware.RequestTimezoneMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lvjiujitsu.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "system.context_processors.system_layout",
            ],
        },
    }
]

WSGI_APPLICATION = "lvjiujitsu.wsgi.application"
ASGI_APPLICATION = "lvjiujitsu.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MANUAL_PAYMENT_PROOF_MAX_SIZE_MB = int(os.getenv("MANUAL_PAYMENT_PROOF_MAX_SIZE_MB", "5"))
MANUAL_PAYMENT_PROOF_ALLOWED_EXTENSIONS = [
    item.strip()
    for item in os.getenv("MANUAL_PAYMENT_PROOF_ALLOWED_EXTENSIONS", "pdf,png,jpg,jpeg").split(",")
    if item.strip()
]
CASH_CLOSURE_ALERT_THRESHOLD = os.getenv("CASH_CLOSURE_ALERT_THRESHOLD", "20.00")
CRITICAL_EXPORT_CONTROL_FILE = os.getenv(
    "CRITICAL_EXPORT_CONTROL_FILE",
    str(BASE_DIR / "exports" / "control" / "critical_exports.flag"),
)
REPORT_EXPORTS_DIR = os.getenv("REPORT_EXPORTS_DIR", str(BASE_DIR / "media" / "exports"))
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_API_VERSION = os.getenv("STRIPE_API_VERSION", "2026-02-25.clover")
STRIPE_CHECKOUT_SUCCESS_PATH = os.getenv("STRIPE_CHECKOUT_SUCCESS_PATH", "/portal/financeiro/minhas-faturas/")
STRIPE_CHECKOUT_CANCEL_PATH = os.getenv("STRIPE_CHECKOUT_CANCEL_PATH", "/portal/financeiro/minhas-faturas/")
STRIPE_CUSTOMER_PORTAL_RETURN_PATH = os.getenv(
    "STRIPE_CUSTOMER_PORTAL_RETURN_PATH",
    "/portal/financeiro/minhas-faturas/",
)
STRIPE_PAUSE_COLLECTION_BEHAVIOR = os.getenv("STRIPE_PAUSE_COLLECTION_BEHAVIOR", "mark_uncollectible")

if DJSTRIPE_ENABLED:
    DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
    DJSTRIPE_WEBHOOK_SECRET = STRIPE_WEBHOOK_SECRET
    DJSTRIPE_USE_NATIVE_JSONFIELD = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1

AUTH_USER_MODEL = "system.SystemUser"
AUTHENTICATION_BACKENDS = [
    "system.backends.CpfAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "none"

LOGIN_URL = "system:login"
LOGIN_REDIRECT_URL = "system:portal-dashboard"
LOGOUT_REDIRECT_URL = "system:home"

AUTH_LOGIN_MAX_FAILED_ATTEMPTS = int(os.getenv("AUTH_LOGIN_MAX_FAILED_ATTEMPTS", "5"))
AUTH_LOGIN_LOCK_MINUTES = int(os.getenv("AUTH_LOGIN_LOCK_MINUTES", "5"))

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = USE_SECURE_COOKIES
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = USE_SECURE_COOKIES
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("DATA_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024)))

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.getenv("DJANGO_DEFAULT_FROM_EMAIL", "noreply@lvjiujitsu.local")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "true").lower() == "true"
CELERY_TASK_EAGER_PROPAGATES = True

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
