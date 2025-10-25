"""Testing module for walletauth app apps module."""

from django.apps import AppConfig

from walletauth.apps import WalletauthConfig


class TestWalletauthApps:
    """Testing class for :py:mod:`walletauth.apps` module."""

    # # WalletauthConfig
    def test_walletauth_apps_walletauthconfig_is_subclass_of_appconfig(self):
        assert issubclass(WalletauthConfig, AppConfig)

    def test_walletauth_apps_walletauthconfig_sets_name(self):
        assert WalletauthConfig.name == "walletauth"
