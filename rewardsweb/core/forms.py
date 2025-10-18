"""Module containing code dealing with core app's forms."""

from django.contrib.auth.models import User
from django.forms import (
    BaseInlineFormSet,
    CharField,
    CheckboxSelectMultiple,
    ChoiceField,
    MultipleChoiceField,
    Form,
    RadioSelect,
    Textarea,
    TextInput,
    ValidationError,
)
from django.forms.models import ModelForm, inlineformset_factory

from core.models import Profile
from utils.constants.core import (
    ISSUE_CREATION_LABEL_CHOICES,
    ISSUE_PRIORITY_CHOICES,
    TOO_LONG_USER_FIRST_NAME_ERROR,
    TOO_LONG_USER_LAST_NAME_ERROR,
)


class CreateIssueForm(Form):
    """TODO: docstring and tests"""

    multiple_labels = MultipleChoiceField(
        choices=ISSUE_CREATION_LABEL_CHOICES,
        widget=CheckboxSelectMultiple(),
        label="Select labels",
        required=True,
    )
    priority = ChoiceField(
        choices=ISSUE_PRIORITY_CHOICES,
        widget=RadioSelect(),
        label="Priority level",
        required=True,
        initial="medium priority",
    )
    issue_body = CharField(
        widget=Textarea(
            attrs={
                "class": "textarea textarea-bordered w-full h-32",
                "placeholder": "Enter issue body text here...",
            }
        ),
        label="Body",
        max_length=500,
        required=True,
    )
    issue_title = CharField(
        max_length=100,
        label="Title",
        widget=TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Enter issue title...",
            }
        ),
        required=True,
    )

    def clean_multiple_labels(self):
        """TODO: docstring and tests"""
        data = self.cleaned_data["multiple_labels"]
        if len(data) < 1:
            raise ValidationError("Please select at least one option.")
        return data

    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation logic here
        return cleaned_data


# # PROFILE
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
