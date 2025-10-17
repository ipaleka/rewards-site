"""Module containing core app adapters."""

from allauth.account.adapter import DefaultAccountAdapter


class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """Not open for signup."""
        return False
