"""Module containing core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Main class for core application.

    :var CoreConfig.name: app name
    :type CoreConfig.name: str
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
