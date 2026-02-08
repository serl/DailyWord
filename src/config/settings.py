from pathlib import Path
from urllib.parse import ParseResult, urlparse

from environs import Env

CONFIG_DIR = Path(__file__).resolve(strict=True).parent
BASE_DIR = CONFIG_DIR.parent.parent

env = Env(eager=False)
env.read_env(str(BASE_DIR / ".env"), recurse=False, override=True)

# SECURITY WARNING: define the correct hosts in production!
BASE_URL: ParseResult = env.url("BASE_URL", default=urlparse("http://127.0.0.1:8000"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY", "django-insecure-vv-293486")

ALLOWED_HOSTS = [
    "localhost",
    BASE_URL.hostname,
    *env.list("ALLOWED_HOSTS", default=[]),
]
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
CSRF_USE_SESSIONS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if BASE_URL.scheme == "https":  # pragma: no cover
    SECURE_HSTS_SECONDS = 2592000
    SECURE_SSL_REDIRECT = True
    SECURE_SSL_HOST = BASE_URL.hostname
    SESSION_COOKIE_SECURE = True
    if env.bool("SECURE_PROXY_SSL_HEADER", default=False):
        # https://docs.djangoproject.com/en/6.0/ref/settings/#std-setting-SECURE_PROXY_SSL_HEADER
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SILENCED_SYSTEM_CHECKS = [
    "security.W005",  # HSTS on subdomains. We're not ready yet.
    "security.W021",  # HSTS preload. Depends on the above.
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "dailyword",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [CONFIG_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL",
        default=f"sqlite:////{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    ),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    CONFIG_DIR / "static",
]

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

STORAGES = {
    "default": {
        # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

WHITENOISE_KEEP_ONLY_HASHED_FILES = True
WHITENOISE_ROOT = CONFIG_DIR / "static_root"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            # Removing "django" logger handlers to avoid double logging with root logger
            "handlers": [],
        },
    },
}

# Email configuration
if DEBUG:  # pragma: no cover
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # https://github.com/migonzalvar/dj-email-url
    email_config = env.dj_email_url("EMAIL_URL", default="dummy:")
    EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
    EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
    EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
    EMAIL_HOST = email_config["EMAIL_HOST"]
    EMAIL_PORT = email_config["EMAIL_PORT"]
    EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
    EMAIL_USE_TLS = email_config["EMAIL_USE_TLS"]
    EMAIL_USE_SSL = email_config["EMAIL_USE_SSL"]
    EMAIL_TIMEOUT = email_config["EMAIL_TIMEOUT"]

    DEFAULT_FROM_EMAIL = env.str(
        "DEFAULT_FROM_EMAIL",
        default=f"noreply@{BASE_URL.hostname}",
    )
    SERVER_EMAIL = DEFAULT_FROM_EMAIL


# Cache configuration
# https://github.com/epicserve/django-cache-url
CACHES = {
    "default": env.dj_cache_url("CACHE_URL", default="locmem://"),
}


# OpenRouter API configuration
OPENROUTER_API_KEY = env.str("OPENROUTER_API_KEY", default="")
OPENROUTER_TEXT_MODEL = env.str("OPENROUTER_TEXT_MODEL", default="openrouter/free")

env.seal()
