"""Testing module for core app apps module."""

from django.apps import AppConfig

from core.apps import CoreConfig


class TestCoreApps:
    """Testing class for :py:mod:`rewardsweb.core.apps` module."""

    # # CoreConfig
    def test_core_apps_coreconfig_is_subclass_of_appconfig(self):
        assert issubclass(CoreConfig, AppConfig)

    def test_core_apps_coreconfig_sets_name(self):
        assert CoreConfig.name == "core"
