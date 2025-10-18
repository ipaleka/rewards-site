"""Testing module for :py:mod:`utils.helpers` module."""

import os

import pytest
from django.core.exceptions import ImproperlyConfigured

from utils.constants.core import MISSING_ENVIRONMENT_VARIABLE_ERROR
from utils.helpers import get_env_variable, parse_full_handle, user_display


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
