"""Testing module for :py:mod:`core.forms` module."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.forms import BaseInlineFormSet, CharField, ModelForm

from core.forms import ProfileFormSet, ProfileInlineForm, UpdateUserForm
from core.models import Profile
from utils.constants.core import (
    TOO_LONG_USER_FIRST_NAME_ERROR,
    TOO_LONG_USER_LAST_NAME_ERROR,
)


# # CORE
class TestUpdateUserForm:
    """Testing class for :class:`UpdateUserForm`."""

    # # UpdateUserForm
    def test_updateuserform_issubclass_of_modelform(self):
        assert issubclass(UpdateUserForm, ModelForm)

    # # Meta
    def test_updateuserform_meta_fields(self):
        form = UpdateUserForm()
        assert form._meta.fields == ("first_name", "last_name")

    def test_updateuserform_meta_model_is_user(self):
        form = UpdateUserForm()
        assert form._meta.model == User

    def test_updateuserform_first_name_field_has_suggestion_as_label(self):
        form = UpdateUserForm()
        assert form.fields["first_name"].label == "First name"

    def test_updateuserform_last_name_field_has_suggestion_as_label(self):
        form = UpdateUserForm()
        assert form.fields["last_name"].label == "Last name"

    def test_updateuserform_form_validation_for_too_long_user_first_name(self):
        form = UpdateUserForm(data={"first_name": "xyz" * 51, "last_name": "last_name"})
        assert form.is_valid() is False
        assert form.errors["first_name"] == [TOO_LONG_USER_FIRST_NAME_ERROR]

    def test_updateuserform_form_validation_for_too_long_user_last_name(self):
        form = UpdateUserForm(data={"first_name": "first_name", "last_name": "x" * 151})
        assert form.is_valid() is False
        assert form.errors["last_name"] == [TOO_LONG_USER_LAST_NAME_ERROR]

    # # save
    @pytest.mark.django_db
    def test_updateuserform_save(self):
        user_model = get_user_model()
        user = user_model.objects.create(email="edituser@example.com")
        form = UpdateUserForm(data={"first_name": "John", "last_name": "Doe"})
        form.instance = user
        form.save()
        assert user_model.objects.all()[0].first_name == "John"


class TestProfileInlineForm:
    """Testing class for :class:`ProfileInlineForm`."""

    # # ProfileInlineForm
    def test_profileinlineform_issubclass_of_baseinlineformset(self):
        assert issubclass(ProfileInlineForm, BaseInlineFormSet)


class TestProfileFormSet:
    """Testing class for ProfileFormSet instance."""

    def test_profileformset_instance_is_user(self):
        formset = ProfileFormSet()
        assert isinstance(formset.instance, User)

    def test_profileformset_model_is_profile(self):
        formset = ProfileFormSet()
        assert formset.model == Profile

    def test_profileformset_address_field(self):
        formset = ProfileFormSet()
        assert "github_token" in formset.form.base_fields
        assert isinstance(formset.github_token, CharField)
        assert formset.github_token.widget.attrs == {"maxlength": "100"}
