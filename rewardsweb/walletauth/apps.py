"""Module containing walletauth app configuration."""

from django.apps import AppConfig


class WalletauthConfig(AppConfig):
    """Main class for core application.

    :var WalletauthConfig.name: app name
    :type WalletauthConfig.name: str
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "walletauth"
