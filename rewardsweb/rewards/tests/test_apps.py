"""Testing module for rewards app apps module."""

from django.apps import AppConfig

from rewards.apps import RewardsConfig


class TestWalletauthApps:
    """Testing class for :py:mod:`rewards.apps` module."""

    # # WalletauthConfig
    def test_rewards_apps_rewardsconfig_is_subclass_of_appconfig(self):
        assert issubclass(RewardsConfig, AppConfig)

    def test_rewards_apps_rewardsconfig_sets_name(self):
        assert RewardsConfig.name == "rewards"
