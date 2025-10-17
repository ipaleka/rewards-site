"""Testing module for core app apps module."""

import sys

from django.apps import AppConfig

import core.apps
from core.apps import CoreConfig


class TestCoreApps:
    """Testing class for :py:mod:`core.apps` module."""

    # # CoreConfig
    def test_core_apps_coreconfig_is_subclass_of_appconfig(self):
        assert issubclass(CoreConfig, AppConfig)

    def test_core_apps_coreconfig_sets_name(self):
        assert CoreConfig.name == "core"

    # # ready
    def test_core_apps_ready_imports_core_signals(self):
        app = CoreConfig("core", core.apps)
        del sys.modules["core.signals"]
        assert "core.signals" not in sys.modules
        app.ready()
        assert "core.signals" in sys.modules
