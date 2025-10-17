"""Module containing code dealing with core app's forms."""

from django.contrib.auth.models import User
from django.forms import BaseInlineFormSet, CharField
from django.forms.models import ModelForm, inlineformset_factory
from django.forms.widgets import TextInput

from core.models import Profile
from utils.constants.core import (
    TOO_LONG_USER_FIRST_NAME_ERROR,
    TOO_LONG_USER_LAST_NAME_ERROR,
)


# # CORE
class UpdateUserForm(ModelForm):
    """Model form class for editing user's data."""

    class Meta:
        model = User
        fields = ("first_name", "last_name")
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
        }
        error_messages = {
            "first_name": {
                "max_length": TOO_LONG_USER_FIRST_NAME_ERROR,
            },
            "last_name": {
                "max_length": TOO_LONG_USER_LAST_NAME_ERROR,
            },
        }


class ProfileInlineForm(BaseInlineFormSet):
    """Form class for editing user profile's data.

    :var github_token: user's GitHub access token
    :type github_token: str
    """

    github_token = CharField(required=False, max_length=100)

    class Meta:
        model = Profile
        fields = ["github_token"]


ProfileFormSet = inlineformset_factory(
    User,
    Profile,
    formset=ProfileInlineForm,
    fields=("github_token",),
)
"""Formset for editing profile's data.
It is instantiated together with :class:`UpdateUserForm` form instance
in the common user/profile editing process.
"""
