"""Django settings module used in production."""

from .base import *

DEBUG = False
ADMINS = [("Edi Ravnic", "info@asastats.com"),]

ALLOWED_HOSTS = [
    "127.0.0.1",
    "144.91.85.65",
    "localhost",
    ".asastats.link",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.asastats.com",
    "https://*.asastats.link",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "service": "rewards_service",
            "passfile": get_env_variable("PGPASSFILE"),
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
            "filename": BASE_DIR.parent / "logs" / "django-warning.log"
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
