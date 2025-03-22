"""Django settings module used in development."""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# # NOTE: db-based tests can't be (yet) done using database setting
#         involving "service" and "passfile" options
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env_variable("DATABASE_NAME"),
        "USER": get_env_variable("DATABASE_USER"),
        "PASSWORD": get_env_variable("DATABASE_PASSWORD"),
        "HOST": "127.0.0.1",
        "PORT": "",  # '5432',
    }
}

STATICFILES_DIRS = [
    BASE_DIR.parent / "static",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
