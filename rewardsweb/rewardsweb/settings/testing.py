"""Django settings module used in production."""

from .base import *

DEBUG = False
ADMINS = [
    ("Eduard Ravnić", "info@asastats.com"),
    ("Ivica Paleka", "ipaleka@asastats.com"),
]

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

MIDDLEWARE.insert(2, "django.middleware.gzip.GZipMiddleware")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "service": "rewardsweb_service",
            "passfile": get_env_variable("PGPASSFILE", "test"),
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

COOKIE_ARGUMENTS = {"domain": "rewards.asastats.com"}

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": BASE_DIR.parent.parent.parent / "logs" / "django-warning.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": True,
        },
    },
}
