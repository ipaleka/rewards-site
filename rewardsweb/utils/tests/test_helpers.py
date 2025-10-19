"""Testing module for :py:mod:`utils.helpers` module."""

import os

import pytest
from django.core.exceptions import ImproperlyConfigured

from utils.constants.core import MISSING_ENVIRONMENT_VARIABLE_ERROR
from utils.helpers import (
    get_env_variable,
    humanize_contributions,
    parse_full_handle,
    user_display,
)


class TestUtilsHelpersFunctions:
    """Testing class for :py:mod:`utils.helpers` functions."""

    # # get_env_variable
    def test_utils_helpers_get_env_variable_access_and_returns_os_environ_key(self):
        var_name = "SECRET_KEY"
        old_value = os.environ[var_name]
        value = "some value"
        os.environ[var_name] = value
        returned = get_env_variable(var_name)
        os.environ[var_name] = old_value
        assert returned == value

    def test_utils_helpers_get_env_variable_raises_for_wrong_variable(self):
        name = "NON_EXISTING_VARIABLE_NAME"
        with pytest.raises(ImproperlyConfigured) as exception:
            get_env_variable(name)
        assert str(exception.value) == "{} {}!".format(
            name, MISSING_ENVIRONMENT_VARIABLE_ERROR
        )

    def test_utils_helpers_get_env_variable_returns_default(self):
        name = "NON_EXISTING_VARIABLE_NAME"
        default = "default"
        assert get_env_variable(name, default) == default

    def test_utils_helpers_get_env_variable_functionality(self):
        assert "settings" in get_env_variable("DJANGO_SETTINGS_MODULE")

    # # humanize_contributions
    def test_utils_helpers_humanize_contributions_empty_queryset(self, mocker):
        contributions = mocker.MagicMock()
        contributions.__iter__ = mocker.MagicMock(return_value=iter([]))

        result = humanize_contributions(contributions)

        assert result == []

    def test_utils_helpers_humanize_contributions_single_contribution(self, mocker):
        contribution = mocker.MagicMock()
        contribution.id = 1
        contribution.contributor.name = "John Doe"
        contribution.cycle.id = 5
        contribution.platform.name = "GitHub"
        contribution.url = "https://github.com/test/repo"
        contribution.reward.type = "Bug Fix"
        contribution.reward.level = "A"
        contribution.percentage = "25.50"
        contribution.reward.amount = "100.00"
        contribution.confirmed = True

        contributions = mocker.MagicMock()
        contributions.__iter__ = mocker.MagicMock(return_value=iter([contribution]))

        result = humanize_contributions(contributions)

        expected = [
            {
                "id": 1,
                "contributor_name": "John Doe",
                "cycle_id": 5,
                "platform": "GitHub",
                "url": "https://github.com/test/repo",
                "type": "Bug Fix",
                "level": "A",
                "percentage": "25.50",
                "reward": "100.00",
                "confirmed": True,
            }
        ]
        assert result == expected

    def test_utils_helpers_humanize_contributions_multiple_contributions(self, mocker):
        contribution1 = mocker.MagicMock()
        contribution1.id = 1
        contribution1.contributor.name = "John Doe"
        contribution1.cycle.id = 5
        contribution1.platform.name = "GitHub"
        contribution1.url = "https://github.com/test/repo"
        contribution1.reward.type = "Bug Fix"
        contribution1.reward.level = "A"
        contribution1.percentage = "25.50"
        contribution1.reward.amount = "100.00"
        contribution1.confirmed = True

        contribution2 = mocker.MagicMock()
        contribution2.id = 2
        contribution2.contributor.name = "Jane Smith"
        contribution2.cycle.id = 5
        contribution2.platform.name = "Discord"
        contribution2.url = "https://discord.com/test"
        contribution2.reward.type = "Feature"
        contribution2.reward.level = "B"
        contribution2.percentage = "15.25"
        contribution2.reward.amount = "75.50"
        contribution2.confirmed = False

        contributions = mocker.MagicMock()
        contributions.__iter__ = mocker.MagicMock(
            return_value=iter([contribution1, contribution2])
        )

        result = humanize_contributions(contributions)

        expected = [
            {
                "id": 1,
                "contributor_name": "John Doe",
                "cycle_id": 5,
                "platform": "GitHub",
                "url": "https://github.com/test/repo",
                "type": "Bug Fix",
                "level": "A",
                "percentage": "25.50",
                "reward": "100.00",
                "confirmed": True,
            },
            {
                "id": 2,
                "contributor_name": "Jane Smith",
                "cycle_id": 5,
                "platform": "Discord",
                "url": "https://discord.com/test",
                "type": "Feature",
                "level": "B",
                "percentage": "15.25",
                "reward": "75.50",
                "confirmed": False,
            },
        ]
        assert result == expected

    def test_utils_helpers_humanize_contributions_with_none_values(self, mocker):
        contribution = mocker.MagicMock()
        contribution.id = 1
        contribution.contributor.name = None
        contribution.cycle.id = None
        contribution.platform.name = None
        contribution.url = None
        contribution.reward.type = None
        contribution.reward.level = None
        contribution.percentage = None
        contribution.reward.amount = None
        contribution.confirmed = None

        contributions = mocker.MagicMock()
        contributions.__iter__ = mocker.MagicMock(return_value=iter([contribution]))

        result = humanize_contributions(contributions)

        expected = [
            {
                "id": 1,
                "contributor_name": None,
                "cycle_id": None,
                "platform": None,
                "url": None,
                "type": None,
                "level": None,
                "percentage": None,
                "reward": None,
                "confirmed": None,
            }
        ]
        assert result == expected

    def test_utils_helpers_humanize_contributions_verify_all_fields_present(
        self, mocker
    ):
        contribution = mocker.MagicMock()
        contribution.id = 1
        contribution.contributor.name = "Test User"
        contribution.cycle.id = 1
        contribution.platform.name = "Test Platform"
        contribution.url = "https://test.com"
        contribution.reward.type = "Test Type"
        contribution.reward.level = "C"
        contribution.percentage = "10.00"
        contribution.reward.amount = "50.00"
        contribution.confirmed = False

        contributions = mocker.MagicMock()
        contributions.__iter__ = mocker.MagicMock(return_value=iter([contribution]))

        result = humanize_contributions(contributions)

        assert len(result) == 1
        humanized = result[0]
        assert "id" in humanized
        assert "contributor_name" in humanized
        assert "cycle_id" in humanized
        assert "platform" in humanized
        assert "url" in humanized
        assert "type" in humanized
        assert "level" in humanized
        assert "percentage" in humanized
        assert "reward" in humanized
        assert "confirmed" in humanized
        assert len(humanized.keys()) == 10  # Verify no extra fields

    # # parse_full_handle
    @pytest.mark.parametrize(
        "full_handle,prefix,handle",
        [
            ("u/user1", "u/", "user1"),
            ("address", "", "address"),
            ("g@address", "g@", "address"),
            ("handle", "", "handle"),
            ("@handle", "@", "handle"),
            ("u/username", "u/", "username"),
            ("username", "", "username"),
            ("@address", "@", "address"),
            ("t@handle", "t@", "handle"),
            ("g@handle", "g@", "handle"),
        ],
    )
    def test_core_modelsparse_full_handle_functionality(
        self, full_handle, prefix, handle
    ):
        assert parse_full_handle(full_handle) == (prefix, handle)

    # # user_display
    def test_utils_userhelpers_user_display_calls_and_returns_profile_name(
        self, mocker
    ):
        user = mocker.MagicMock()
        returned = user_display(user)
        assert returned == user.profile.name
