"""Testing module for :py:mod:`core.admin` module."""

import importlib
from unittest import mock

from core import admin
from core.models import (
    Contribution,
    Contributor,
    Cycle,
    Handle,
    Reward,
    RewardType,
    SocialPlatform,
)


class TestCoreAdmin:
    """Testing class for :py:mod:`core.admin` module."""

    # # REGISTER
    def test_core_admin_registers_model(self):
        with mock.patch("core.admin.admin.site.register") as mocked_register:
            importlib.reload(admin)
            calls = [
                mock.call(Contribution),
                mock.call(Contributor),
                mock.call(Cycle),
                mock.call(Handle),
                mock.call(Reward),
                mock.call(RewardType),
                mock.call(SocialPlatform),
            ]
            mocked_register.assert_has_calls(calls, any_order=True)
            assert mocked_register.call_count == 7
