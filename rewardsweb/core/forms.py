"""Module containing code dealing with core app's forms."""

from django.contrib.auth.models import User
from django.forms import (
    CharField,
    CheckboxSelectMultiple,
    ChoiceField,
    DecimalField,
    Form,
    ModelChoiceField,
    MultipleChoiceField,
    NumberInput,
    RadioSelect,
    Select,
    Textarea,
    TextInput,
    ValidationError,
)
from django.forms.models import ModelForm, inlineformset_factory

from core.models import Contribution, Profile, Reward
from utils.constants.core import ISSUE_CREATION_LABEL_CHOICES, ISSUE_PRIORITY_CHOICES
from utils.constants.ui import MISSING_OPTION_TEXT, TEXTINPUT_CLASS


class ContributionEditForm(ModelForm):
    """Model form class for editing contribution data.

    :var ContributionEditForm.reward: reward type for the contribution
    :type ContributionEditForm.reward: :class:`django.forms.ModelChoiceField`
    :var ContributionEditForm.percentage: percentage value for the contribution
    :type ContributionEditForm.percentage: :class:`django.forms.DecimalField`
    :var ContributionEditForm.comment: optional comment for the contribution
    :type ContributionEditForm.comment: :class:`django.forms.CharField`
    """

    reward = ModelChoiceField(
        queryset=Reward.objects.filter(active=True),
        empty_label="Select a reward type",
        widget=Select(attrs={"class": "select select-bordered w-full"}),
    )
    percentage = DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=NumberInput(
            attrs={
                "class": TEXTINPUT_CLASS,
                "step": "0.01",
                "min": "0",
                "max": "100",
            }
        ),
    )
    comment = CharField(
        required=False, widget=TextInput(attrs={"class": TEXTINPUT_CLASS})
    )

    class Meta:
        model = Contribution
        fields = ["reward", "percentage", "comment"]


class ContributionInvalidateForm(ModelForm):
    """Model form class for setting contribution as already existing.

    :var ContributionInvalidateForm.comment: optional comment to add as a reply
    :type ContributionInvalidateForm.comment: :class:`django.forms.CharField`
    """

    comment = CharField(
        widget=Textarea(
            attrs={
                "class": "textarea textarea-bordered w-full h-32",
                "placeholder": "Enter comment text here...",
            }
        ),
        label="Reply",
        max_length=500,
        required=False,
    )

    class Meta:
        model = Contribution
        fields = ["comment"]


class CreateIssueForm(Form):
    """Form class for creating GitHub issues.

    :var CreateIssueForm.labels: issue labels selection
    :type CreateIssueForm.labels: :class:`django.forms.MultipleChoiceField`
    :var CreateIssueForm.priority: issue priority level
    :type CreateIssueForm.priority: :class:`django.forms.ChoiceField`
    :var CreateIssueForm.issue_title: title of the issue
    :type CreateIssueForm.issue_title: :class:`django.forms.CharField`
    :var CreateIssueForm.issue_body: body content of the issue
    :type CreateIssueForm.issue_body: :class:`django.forms.CharField`
    """

    labels = MultipleChoiceField(
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
    issue_title = CharField(
        max_length=100,
        label="Title",
        widget=TextInput(
            attrs={
                "class": TEXTINPUT_CLASS,
                "placeholder": "Enter issue title...",
            }
        ),
        required=True,
    )
    issue_body = CharField(
        widget=Textarea(
            attrs={
                "class": "textarea textarea-bordered w-full h-32",
                "placeholder": "Enter issue body text here...",
            }
        ),
        label="Body",
        max_length=2000,
        required=True,
    )

    def clean_labels(self):
        """Ensure at least one label is selected.

        Raise ValidationError if no labels are selected.

        :var data: collection of form data
        :type data: dict
        :return: dict
        """
        data = self.cleaned_data["labels"]
        if len(data) < 1:
            raise ValidationError(MISSING_OPTION_TEXT)

        return data


class IssueLabelsForm(Form):
    """Form for adding labels and priority to GitHub issues.

    :var IssueLabelsForm.labels: issue labels selection
    :type IssueLabelsForm.labels: :class:`django.forms.MultipleChoiceField`
    :var IssueLabelsForm.priority: issue priority level
    :type IssueLabelsForm.priority: :class:`django.forms.ChoiceField`
    """

    labels = MultipleChoiceField(
        choices=ISSUE_CREATION_LABEL_CHOICES,
        widget=CheckboxSelectMultiple(),
        required=True,
    )
    priority = ChoiceField(
        choices=ISSUE_PRIORITY_CHOICES,
        widget=RadioSelect(),
        required=True,
        initial="medium priority",
    )

    def clean_labels(self):
        """Ensure at least one label is selected.

        Raise ValidationError if no labels are selected.

        :var data: collection of form data
        :type data: dict
        :return: dict
        """
        data = self.cleaned_data["labels"]
        if len(data) < 1:
            raise ValidationError(MISSING_OPTION_TEXT)

        return data


# # PROFILE
class UpdateUserForm(ModelForm):
    """Model form class for editing user's data.

    :var UpdateUserForm.first_name: user's first name field
    :type UpdateUserForm.first_name: :class:`django.forms.CharField`
    :var UpdateUserForm.last_name: user's last name field
    :type UpdateUserForm.last_name: :class:`django.forms.CharField`
    """

    first_name = CharField(
        required=False,
        widget=TextInput(
            attrs={
                "class": TEXTINPUT_CLASS,
                "placeholder": "Enter your first name",
            }
        ),
    )
    last_name = CharField(
        required=False,
        widget=TextInput(
            attrs={
                "class": TEXTINPUT_CLASS,
                "placeholder": "Enter your last name",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ProfileForm(ModelForm):
    """Form class for editing user profile's data.

    :var ProfileForm.github_token: user's personal GitHub access token
    :type ProfileForm.github_token: :class:`django.forms.CharField`
    """

    github_token = CharField(
        required=False,
        widget=TextInput(
            attrs={
                "class": TEXTINPUT_CLASS,
                "placeholder": "Enter your GitHub token (optional)",
            }
        ),
        help_text="Optional: GitHub personal access token for accessing issues",
    )

    class Meta:
        model = Profile
        fields = ["github_token"]
        exclude = ["user"]


ProfileFormSet = inlineformset_factory(
    User, Profile, form=ProfileForm, extra=1, can_delete=False, max_num=1
)
"""Formset for editing profile's data.
It is instantiated together with :class:`UpdateUserForm` form instance
in the common user/profile editing process.
"""
