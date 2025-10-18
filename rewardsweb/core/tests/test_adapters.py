"""Testing module for :py:mod:`core.adapters` module."""

from allauth.account.adapter import DefaultAccountAdapter

from core.adapters import NoSignupAccountAdapter


class TestCoreAdapters:
    """Testing class for :py:mod:`core.adapters` module."""

    # # NoSignupAccountAdapter
    def test_core_adapters_nosignupaccountadapter_is_subclass_of_defaultaccountadapter(
        self,
    ):
        assert issubclass(NoSignupAccountAdapter, DefaultAccountAdapter)

    # # is_open_for_signup
    def test_core_adapters_nosignupaccountadapter_is_open_for_signup_functionality(
        self,
    ):
        assert NoSignupAccountAdapter().is_open_for_signup(None) is False
