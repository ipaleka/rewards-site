"""Testing module for :py:mod:`core.views` module."""

import time
from datetime import datetime

import pytest
from allauth.account.forms import LoginForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from core.models import (
    Contribution,
    Contributor,
    Cycle,
    Handle,
    Issue,
    IssueStatus,
    SocialPlatform,
)
from core.forms import (
    ContributionEditForm,
    ContributionInvalidateForm,
    IssueLabelsForm,
    ProfileFormSet,
    UpdateUserForm,
)
from core.views import (
    ContributionDetailView,
    ContributionEditView,
    ContributionInvalidateView,
    ContributorListView,
    ContributorDetailView,
    CreateIssueView,
    CycleListView,
    CycleDetailView,
    IndexView,
    IssueDetailView,
    IssueListView,
    ProfileDisplay,
    ProfileEditView,
    ProfileUpdate,
)
from utils.constants.core import DISCORD_EMOJIS

user_model = get_user_model()


# # HELPERS
def get_user_edit_fake_post_data(user, first_name="first_name", last_name="last_name"):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "csrfmiddlewaretoken": "ebklx66wgoqT9kReeo67yxdCyzG2EtoBIRDvGjShzWfvbAnOhsdC4dok2vNta0PQ",
        "profile-TOTAL_FORMS": 1,
        "profile-INITIAL_FORMS": 1,
        "profile-MIN_NUM_FORMS": 0,
        "profile-MAX_NUM_FORMS": 1,
        "profile-0-address": "",
        "profile-0-authorized": False,
        "profile-0-permission": 0,
        "profile-0-currency": "ALGO",
        "profile-0-id": user.profile.id,
        "profile-0-user": user.id,
        "_mutable": False,
    }


class BaseView:
    """Base helper class for testing custom views."""

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same as those passed to ``reverse()``

        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    # # helper methods
    def setup_method(self):
        # Setup request
        self.request = RequestFactory().get("/fake-path")


class BaseUserCreatedView(BaseView):
    def setup_method(self):
        # # Setup user
        username = "user{}".format(str(time.time())[5:])
        self.user = user_model.objects.create(
            email="{}@testuser.com".format(username),
            username=username,
        )
        # Setup request
        self.request = RequestFactory().get("/fake-path")
        self.request.user = self.user


class IndexPageTest(TestCase):
    def post_invalid_input(self):
        return self.client.post(reverse("index"), data={"address": "foobar"})

    def test_index_page_renders_index_template(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")


class TestIndexView:
    """Testing class for :class:`core.views.IndexView`."""

    def test_indexview_is_subclass_of_listview(self):
        assert issubclass(IndexView, ListView)

    def test_indexview_model(self):
        view = IndexView()
        assert view.model == Contribution

    def test_indexview_paginate_by(self):
        view = IndexView()
        assert view.paginate_by == 20

    def test_indexview_template_name(self):
        view = IndexView()
        assert view.template_name == "index.html"


@pytest.mark.django_db
class TestDbIndexView:
    """Testing class for :class:`core.views.IndexView` with database."""

    def test_indexview_get_queryset(self, contribution):
        # Create a confirmed contribution that should not appear
        Contribution.objects.create(
            contributor=contribution.contributor,
            cycle=contribution.cycle,
            platform=contribution.platform,
            reward=contribution.reward,
            percentage=100.0,
            confirmed=True,
        )

        view = IndexView()
        queryset = view.get_queryset()

        # Should only include unconfirmed contributions
        assert queryset.filter(confirmed=True).count() == 0
        assert queryset.filter(confirmed=False).count() == 1

    def test_indexview_get_context_data(self, rf):
        request = rf.get("/")

        # Create test data first
        Cycle.objects.create(start="2023-01-01", end="2023-01-31")
        Cycle.objects.create(start="2023-02-01", end="2023-02-28")
        Contributor.objects.create(name="contributor1", address="addr1")
        Contributor.objects.create(name="contributor2", address="addr2")

        # Setup view properly
        view = IndexView()
        view.setup(request)
        view.object_list = Contribution.objects.none()
        view.request = request

        context = view.get_context_data()

        assert context["num_cycles"] == 2
        assert context["num_contributors"] == 2
        assert context["num_contributions"] == 0
        # When there are no contributions, total_rewards can be None
        assert context["total_rewards"] in [0, None]


class TestContributionDetailView:
    """Testing class for :class:`core.views.ContributionDetailView`."""

    def test_contributiondetailview_is_subclass_of_detailview(self):
        assert issubclass(ContributionDetailView, DetailView)

    def test_contributiondetailview_model(self):
        view = ContributionDetailView()
        assert view.model == Contribution


@pytest.mark.django_db
class TestDbContributionDetailView:
    """Testing class for :class:`core.views.ContributionDetailView` with database."""

    def test_contributiondetailview_get_object(self, rf, contribution):
        request = rf.get(f"/contributions/{contribution.id}/")

        view = ContributionDetailView()
        view.setup(request, pk=contribution.id)

        obj = view.get_object()

        assert obj == contribution
        assert obj.id == contribution.id


class TestContributionEditView:
    """Testing class for :class:`core.views.ContributionEditView`."""

    def test_contributioneditview_is_subclass_of_updateview(self):
        assert issubclass(ContributionEditView, UpdateView)

    def test_contributioneditview_model(self):
        view = ContributionEditView()
        assert view.model == Contribution

    def test_contributioneditview_form_class(self):
        view = ContributionEditView()
        assert view.form_class == ContributionEditForm

    def test_contributioneditview_template_name(self):
        view = ContributionEditView()
        assert view.template_name == "core/contribution_edit.html"


@pytest.mark.django_db
class TestDbContributionEditView:
    """Testing class for :class:`core.views.ContributionEditView` with database."""

    def _setup_messages(self, request):
        """Helper method to setup messages framework for request."""
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    def test_contributioneditview_get_success_url(self, rf, superuser, contribution):
        request = rf.get(f"/contributions/{contribution.id}/edit/")
        request.user = superuser
        request = self._setup_messages(request)

        view = ContributionEditView()
        view.setup(request, pk=contribution.id)
        view.object = contribution
        view.request = request

        success_url = view.get_success_url()

        expected_url = reverse("contribution-detail", kwargs={"pk": contribution.pk})
        assert success_url == expected_url

    def test_contributioneditview_requires_superuser(
        self, rf, regular_user, contribution
    ):
        request = rf.get(f"/contribution/{contribution.id}/edit/")
        request.user = regular_user

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Should redirect to login (302) for non-superusers
        assert response.status_code == 302

    def test_contributioneditview_superuser_access_granted(
        self, rf, superuser, contribution
    ):
        request = rf.get(f"/contribution/{contribution.id}/edit/")
        request.user = superuser

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Should return 200 for superuser
        assert response.status_code == 200

    def test_contributioneditview_form_valid_with_existing_issue(
        self, rf, superuser, contribution, issue
    ):
        request = rf.post(
            f"/contribution/{contribution.id}/edit/",
            {
                "reward": contribution.reward.id,
                "percentage": "50.00",
                "comment": "Test comment",
                "issue_number": issue.number,
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Refresh contribution from database
        contribution.refresh_from_db()

        # Should redirect to success URL
        assert response.status_code == 302
        assert contribution.issue == issue

    def test_contributioneditview_form_valid_with_new_issue(
        self, rf, superuser, contribution, mocker
    ):
        # Mock the GitHub check to return successful issue data
        mock_issue_by_number = mocker.patch(
            "core.views.issue_by_number",
            return_value={"success": True, "data": {"number": 123}},
        )

        request = rf.post(
            f"/contribution/{contribution.id}/edit/",
            {
                "reward": contribution.reward.id,
                "percentage": "50.00",
                "comment": "Test comment",
                "issue_number": "123",
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Refresh contribution from database
        contribution.refresh_from_db()

        # Should redirect to success URL
        assert response.status_code == 302
        assert contribution.issue is not None
        assert contribution.issue.number == 123
        mock_issue_by_number.assert_called_once_with(superuser, 123)

    def test_contributioneditview_form_invalid_with_nonexistent_github_issue(
        self, rf, superuser, contribution, mocker
    ):
        """Test when GitHub issue doesn't exist (success=False, error=MISSING_TOKEN_TEXT)."""
        from core.views import MISSING_TOKEN_TEXT

        # Mock the GitHub check to return failure with "issue doesn't exist" error
        mock_issue_by_number = mocker.patch(
            "core.views.issue_by_number",
            return_value={"success": False, "error": MISSING_TOKEN_TEXT},
        )

        request = rf.post(
            f"/contribution/{contribution.id}/edit/",
            {
                "reward": contribution.reward.id,
                "percentage": "50.00",
                "comment": "Test comment",
                "issue_number": "999",
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Should return form with error (200 status)
        assert response.status_code == 200

        # Check that the form in the context has the expected error
        assert "form" in response.context_data
        form = response.context_data["form"]
        assert "issue_number" in form.errors
        assert "That GitHub issue doesn't exist!" in form.errors["issue_number"]

        mock_issue_by_number.assert_called_once_with(superuser, 999)

    def test_contributioneditview_form_invalid_with_github_api_error(
        self, rf, superuser, contribution, mocker
    ):
        """Test when GitHub API returns a different error (not MISSING_TOKEN_TEXT)."""
        from core.views import MISSING_TOKEN_TEXT

        # Mock the GitHub check to return failure with a different error
        mock_issue_by_number = mocker.patch(
            "core.views.issue_by_number",
            return_value={"success": False, "error": "API rate limit exceeded"},
        )

        request = rf.post(
            f"/contribution/{contribution.id}/edit/",
            {
                "reward": contribution.reward.id,
                "percentage": "50.00",
                "comment": "Test comment",
                "issue_number": "999",
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Should return form with error (200 status)
        assert response.status_code == 200

        # Check that the form in the context has the expected error
        assert "form" in response.context_data
        form = response.context_data["form"]
        assert "issue_number" in form.errors
        assert MISSING_TOKEN_TEXT in form.errors["issue_number"]

        mock_issue_by_number.assert_called_once_with(superuser, 999)

    def test_contributioneditview_form_invalid_with_github_api_missing_token_error(
        self, rf, superuser, contribution, mocker
    ):
        """Test when GitHub API returns MISSING_TOKEN_TEXT error specifically."""
        from core.views import MISSING_TOKEN_TEXT

        # Mock the GitHub check to return failure with MISSING_TOKEN_TEXT
        mock_issue_by_number = mocker.patch(
            "core.views.issue_by_number",
            return_value={"success": False, "error": MISSING_TOKEN_TEXT},
        )

        request = rf.post(
            f"/contribution/{contribution.id}/edit/",
            {
                "reward": contribution.reward.id,
                "percentage": "50.00",
                "comment": "Test comment",
                "issue_number": "999",
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Should return form with error (200 status)
        assert response.status_code == 200

        # Check that the form in the context has the expected error
        assert "form" in response.context_data
        form = response.context_data["form"]
        assert "issue_number" in form.errors
        assert "That GitHub issue doesn't exist!" in form.errors["issue_number"]

        mock_issue_by_number.assert_called_once_with(superuser, 999)

    def test_contributioneditview_form_valid_without_issue_number(
        self, rf, superuser, contribution_with_issue
    ):
        """Test that empty issue_number removes existing issue association."""
        request = rf.post(
            f"/contribution/{contribution_with_issue.id}/edit/",
            {
                "reward": contribution_with_issue.reward.id,
                "percentage": "75.00",
                "comment": "Updated comment",
                "issue_number": "",  # Empty to remove issue
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(
            request, pk=contribution_with_issue.id
        )

        # Refresh contribution from database
        contribution_with_issue.refresh_from_db()

        # Should redirect to success URL and remove issue
        assert response.status_code == 302
        assert contribution_with_issue.issue is None

    def test_contributioneditview_form_valid_with_none_issue_number(
        self, rf, superuser, contribution_with_issue
    ):
        """Test that missing issue_number removes existing issue association."""
        request = rf.post(
            f"/contribution/{contribution_with_issue.id}/edit/",
            {
                "reward": contribution_with_issue.reward.id,
                "percentage": "100.00",
                "comment": "Remove issue test",
                # issue_number not provided (defaults to None)
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(
            request, pk=contribution_with_issue.id
        )

        # Refresh from database
        contribution_with_issue.refresh_from_db()

        # Should redirect and remove issue
        assert response.status_code == 302
        assert contribution_with_issue.issue is None

    def test_contributioneditview_form_valid_creates_new_issue_when_success_true(
        self, rf, superuser, contribution, mocker
    ):
        """Test that new issue is created when GitHub API returns success=True."""
        # Mock the GitHub check to return successful issue data
        mock_issue_by_number = mocker.patch(
            "core.views.issue_by_number",
            return_value={"success": True, "data": {"number": 456}},
        )

        request = rf.post(
            f"/contribution/{contribution.id}/edit/",
            {
                "reward": contribution.reward.id,
                "percentage": "80.00",
                "comment": "Test with new issue",
                "issue_number": "456",
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(request, pk=contribution.id)

        # Refresh contribution from database
        contribution.refresh_from_db()

        # Should redirect to success URL
        assert response.status_code == 302

        # Should create and attach a new issue
        assert contribution.issue is not None
        assert contribution.issue.number == 456
        assert contribution.issue.status == IssueStatus.CREATED

        # Verify the GitHub API was called
        mock_issue_by_number.assert_called_once_with(superuser, 456)

    def test_contributioneditview_form_valid_with_existing_issue_different_number(
        self, rf, superuser, contribution_with_issue
    ):
        """Test updating with a different existing issue number."""
        # Create a different issue
        different_issue = Issue.objects.create(number=789, status=IssueStatus.CREATED)

        request = rf.post(
            f"/contribution/{contribution_with_issue.id}/edit/",
            {
                "reward": contribution_with_issue.reward.id,
                "percentage": "90.00",
                "comment": "Updated with different issue",
                "issue_number": "789",  # Different existing issue
            },
        )
        request.user = superuser
        request = self._setup_messages(request)

        response = ContributionEditView.as_view()(
            request, pk=contribution_with_issue.id
        )

        # Refresh contribution from database
        contribution_with_issue.refresh_from_db()

        # Should redirect to success URL and update to different issue
        assert response.status_code == 302
        assert contribution_with_issue.issue == different_issue
        assert contribution_with_issue.issue.number == 789


class TestContributionInvalidateView:
    """Testing class for :class:`core.views.ContributionInvalidateView`."""

    def test_contributioninvalidateview_is_subclass_of_updateview(self):
        assert issubclass(ContributionInvalidateView, UpdateView)

    def test_contributioninvalidateview_model(self):
        view = ContributionInvalidateView()
        assert view.model == Contribution

    def test_contributioninvalidateview_form_class(self):
        view = ContributionInvalidateView()
        assert view.form_class == ContributionInvalidateForm

    def test_contributioninvalidateview_template_name(self):
        view = ContributionInvalidateView()
        assert view.template_name == "core/contribution_invalidate.html"


@pytest.mark.django_db
class TestContributionInvalidateViewDb:
    """Test suite for ContributionInvalidateView."""

    def test_contributioninvalidateview_superuser_required(
        self, client, regular_user, invalidate_url
    ):
        """Test that only superusers can access the view."""
        client.force_login(regular_user)
        response = client.get(invalidate_url)
        # The view uses @user_passes_test which redirects to login for non-superusers
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_contributioninvalidateview_superuser_can_access(
        self, client, superuser, invalidate_url, mock_message_from_url
    ):
        """Test that superuser can access the view."""
        client.force_login(superuser)
        response = client.get(invalidate_url)
        assert response.status_code == 200

    def test_contributioninvalidateview_get_context_data(
        self, client, superuser, invalidate_url, mock_message_from_url
    ):
        """Test that context contains required data."""
        client.force_login(superuser)
        response = client.get(invalidate_url)

        assert response.status_code == 200
        assert "type" in response.context
        assert "original_comment" in response.context
        assert response.context["type"] == "duplicate"

    @pytest.mark.parametrize(
        "comment,expected_comment",
        [
            ("This is a test reply", "This is a test reply"),
            ("", ""),
        ],
    )
    def test_contributioninvalidateview_form_valid_all_operations_successful(
        self,
        client,
        superuser,
        contribution,
        invalidate_url,
        comment,
        expected_comment,
        mocker,
    ):
        """Test successful form submission with and without comment."""
        client.force_login(superuser)

        mock_add_reply = mocker.patch(
            "core.views.add_reply_to_message", return_value=True
        )
        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message", return_value=True
        )

        response = client.post(invalidate_url, {"comment": comment})

        # Check that operations were called appropriately
        if comment:
            mock_add_reply.assert_called_once_with(contribution.url, expected_comment)
        else:
            mock_add_reply.assert_not_called()

        mock_add_reaction.assert_called_once_with(
            contribution.url, DISCORD_EMOJIS.get("duplicate")
        )

        # Check that contribution was confirmed
        contribution.refresh_from_db()
        assert contribution.confirmed is True

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "successfully" in messages[0].message

        # Check redirect
        expected_url = reverse("contribution-detail", kwargs={"pk": contribution.pk})
        assert response.url == expected_url

    def test_contributioninvalidateview_form_valid_reply_fails(
        self, client, superuser, contribution, invalidate_url, mocker
    ):
        """Test form submission when reply operation fails."""
        client.force_login(superuser)

        mock_add_reply = mocker.patch(
            "core.views.add_reply_to_message", return_value=False
        )
        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message", return_value=True
        )

        response = client.post(invalidate_url, {"comment": "This is a test reply"})

        # Check that contribution was NOT confirmed
        contribution.refresh_from_db()
        assert contribution.confirmed is False

        # Check that form has error and was re-rendered
        assert response.status_code == 200
        content = response.content.decode()
        assert "Failed to add reply" in content or "All operations failed" in content

    def test_contributioninvalidateview_form_valid_reaction_fails(
        self, client, superuser, contribution, invalidate_url, mocker
    ):
        """Test form submission when reaction operation fails."""
        client.force_login(superuser)

        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message", return_value=False
        )

        response = client.post(invalidate_url, {"comment": ""})

        # Check that contribution was NOT confirmed
        contribution.refresh_from_db()
        assert contribution.confirmed is False

        # Check that form has error
        assert response.status_code == 200
        content = response.content.decode()
        # Check for either specific error or general error message
        assert any(
            msg in content
            for msg in ["Failed to add reaction", "All operations failed"]
        )

    def test_contributioninvalidateview_form_valid_both_operations_fail(
        self, client, superuser, contribution, invalidate_url, mocker
    ):
        """Test form submission when both operations fail."""
        client.force_login(superuser)

        mock_add_reply = mocker.patch(
            "core.views.add_reply_to_message", return_value=False
        )
        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message", return_value=False
        )

        response = client.post(invalidate_url, {"comment": "This is a test reply"})

        # Check that contribution was NOT confirmed
        contribution.refresh_from_db()
        assert contribution.confirmed is False

        # Check that form has error
        assert response.status_code == 200
        assert "All operations failed" in response.content.decode()

    def test_contributioninvalidateview_form_valid_reply_exception(
        self, client, superuser, contribution, invalidate_url, mocker
    ):
        """Test form submission when reply operation raises exception."""
        client.force_login(superuser)

        mock_add_reply = mocker.patch(
            "core.views.add_reply_to_message", side_effect=Exception("Reply failed")
        )
        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message", return_value=True
        )

        response = client.post(invalidate_url, {"comment": "This is a test reply"})

        # Check that contribution was NOT confirmed
        contribution.refresh_from_db()
        assert contribution.confirmed is False

        # Check that form has error
        assert response.status_code == 200
        content = response.content.decode()
        assert any(
            msg in content for msg in ["Failed to add reply", "All operations failed"]
        )

    def test_contributioninvalidateview_form_valid_reaction_exception(
        self, client, superuser, contribution, invalidate_url, mocker
    ):
        """Test form submission when reaction operation raises exception."""
        client.force_login(superuser)

        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message",
            side_effect=Exception("Reaction failed"),
        )

        response = client.post(invalidate_url, {"comment": ""})

        # Check that contribution was NOT confirmed
        contribution.refresh_from_db()
        assert contribution.confirmed is False

        # Check that form has error
        assert response.status_code == 200
        content = response.content.decode()
        assert any(
            msg in content
            for msg in ["Failed to add reaction", "All operations failed"]
        )

    @pytest.mark.parametrize("reaction", ["duplicate", "wontfix"])
    def test_contributioninvalidateview_different_types(
        self, client, superuser, contribution, reaction, mocker
    ):
        """Test view works with different type parameters."""
        url = reverse(
            "contribution-invalidate",
            kwargs={"pk": contribution.pk, "reaction": reaction},
        )

        client.force_login(superuser)

        mock_add_reaction = mocker.patch(
            "core.views.add_reaction_to_message", return_value=True
        )

        response = client.post(url, {"comment": ""})

        # Check that reaction was called with correct type
        mock_add_reaction.assert_called_once_with(
            contribution.url, DISCORD_EMOJIS.get(reaction)
        )

        # Check success
        contribution.refresh_from_db()
        assert contribution.confirmed is True

    def test_contributioninvalidateview_form_fields_present(
        self, client, superuser, invalidate_url, mock_message_from_url
    ):
        """Test that form contains expected fields."""
        client.force_login(superuser)
        response = client.get(invalidate_url)

        content = response.content.decode()
        assert 'name="comment"' in content
        assert "textarea" in content
        assert "Set as duplicate" in content

    def test_contributioninvalidateview_original_comment_in_context_message_success(
        self, client, superuser, invalidate_url, mock_message_from_url
    ):
        """Test that original comment is included when message_from_url returns success."""
        client.force_login(superuser)
        response = client.get(invalidate_url)

        assert "original_comment" in response.context
        assert "test_user" in response.context["original_comment"]
        assert "Test message content" in response.context["original_comment"]

    def test_contributioninvalidateview_original_comment_empty_when_message_fails(
        self, client, superuser, contribution, mocker
    ):
        """Test that original comment is empty when message_from_url fails."""
        url = reverse(
            "contribution-invalidate",
            kwargs={"pk": contribution.pk, "reaction": "duplicate"},
        )

        # Mock message_from_url to return failure
        mocker.patch("core.views.message_from_url", return_value={"success": False})

        client.force_login(superuser)
        response = client.get(url)

        # The view should still have original_comment in context, but empty
        assert "original_comment" in response.context
        assert response.context["original_comment"] == ""

    def test_contributioninvalidateview_success_message_content_with_comment(
        self, client, superuser, invalidate_url, mocker
    ):
        """Test success message includes reply information when comment is provided."""
        client.force_login(superuser)

        mocker.patch("core.views.add_reply_to_message", return_value=True)
        mocker.patch("core.views.add_reaction_to_message", return_value=True)

        response = client.post(invalidate_url, {"comment": "Test reply"})

        messages = list(get_messages(response.wsgi_request))
        message_text = messages[0].message.lower()

        assert "reply" in message_text
        assert "reaction" in message_text
        assert "duplicate" in message_text

    def test_contributioninvalidateview_success_message_content_without_comment(
        self, client, superuser, invalidate_url, mocker
    ):
        """Test success message excludes reply information when no comment is provided."""
        client.force_login(superuser)

        mocker.patch("core.views.add_reaction_to_message", return_value=True)

        response = client.post(invalidate_url, {"comment": ""})

        messages = list(get_messages(response.wsgi_request))
        message_text = messages[0].message.lower()

        assert "reply" not in message_text
        assert "reaction" in message_text
        assert "duplicate" in message_text


class TestContributorListView:
    """Testing class for :class:`core.views.ContributorListView`."""

    def test_contributorlistview_is_subclass_of_listview(self):
        assert issubclass(ContributorListView, ListView)

    def test_contributorlistview_model(self):
        view = ContributorListView()
        assert view.model == Contributor

    def test_contributorlistview_paginate_by(self):
        view = ContributorListView()
        assert view.paginate_by == 20


@pytest.mark.django_db
class TestDbContributorListView:
    """Testing class for :class:`core.views.ContributorListView` with database."""

    def test_contributorlistview_queryset(self, rf):
        request = rf.get("/contributors/")

        # Create test contributors
        Contributor.objects.create(name="contributor1", address="addr1")
        Contributor.objects.create(name="contributor2", address="addr2")

        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        assert queryset.count() == 2
        assert all(isinstance(obj, Contributor) for obj in queryset)


class TestContributorListViewSearch:
    """Testing class for :class:`core.views.ContributorListView` search functionality."""

    def test_contributorlistview_search_inheritance(self):
        assert issubclass(ContributorListView, ListView)

    def test_contributorlistview_model(self):
        view = ContributorListView()
        assert view.model == Contributor

    def test_contributorlistview_paginate_by(self):
        view = ContributorListView()
        assert view.paginate_by == 20

    def test_contributorlistview_template_name_suffix(self):
        view = ContributorListView()
        assert view.template_name_suffix == "_list"


@pytest.mark.django_db
class TestDbContributorListViewSearch:
    """Testing class for :class:`core.views.ContributorListView` search with database."""

    def test_contributorlistview_search_by_name(self, rf):
        # Create test contributors
        contributor1 = Contributor.objects.create(name="John Doe", address="addr1")
        contributor2 = Contributor.objects.create(name="Jane Smith", address="addr2")
        contributor3 = Contributor.objects.create(name="Bob Johnson", address="addr3")

        # Create request with search query
        request = rf.get("/contributors/", {"q": "john"})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should find John Doe and Bob Johnson
        assert queryset.count() == 2
        assert contributor1 in queryset
        assert contributor3 in queryset
        assert contributor2 not in queryset

    def test_contributorlistview_search_by_handle(self, rf):
        # Create test contributors
        contributor1 = Contributor.objects.create(name="User1", address="addr1")
        contributor2 = Contributor.objects.create(name="User2", address="addr2")

        # Create social platforms
        github = SocialPlatform.objects.create(name="GitHub", prefix="g@")
        discord = SocialPlatform.objects.create(name="Discord", prefix="")

        # Create handles
        Handle.objects.create(
            contributor=contributor1, platform=github, handle="developer"
        )
        Handle.objects.create(
            contributor=contributor2, platform=discord, handle="tester"
        )

        # Create request with search query
        request = rf.get("/contributors/", {"q": "test"})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should find contributor with "tester" handle
        assert queryset.count() == 1
        assert contributor2 in queryset
        assert contributor1 not in queryset

    def test_contributorlistview_search_by_name_and_handle(self, rf):
        # Create test contributors
        contributor1 = Contributor.objects.create(name="Alice", address="addr1")
        contributor2 = Contributor.objects.create(name="Bob", address="addr2")
        contributor3 = Contributor.objects.create(name="Charlie", address="addr3")

        # Create social platform
        github = SocialPlatform.objects.create(name="GitHub", prefix="g@")

        # Create handles
        Handle.objects.create(
            contributor=contributor1, platform=github, handle="alice_dev"
        )
        Handle.objects.create(
            contributor=contributor2, platform=github, handle="charlie_fan"
        )

        # Create request with search query
        request = rf.get("/contributors/", {"q": "charlie"})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should find Charlie by name and Bob by handle
        assert queryset.count() == 2
        assert contributor2 in queryset  # Has handle "charlie_fan"
        assert contributor3 in queryset  # Name is "Charlie"
        assert contributor1 not in queryset

    def test_contributorlistview_search_case_insensitive(self, rf):
        # Create test contributors
        contributor1 = Contributor.objects.create(name="John Doe", address="addr1")
        contributor2 = Contributor.objects.create(name="Mary Jane", address="addr2")

        # Create social platform
        github = SocialPlatform.objects.create(name="GitHub", prefix="g@")
        Handle.objects.create(
            contributor=contributor2, platform=github, handle="SuperUser"
        )

        # Test different case variations
        test_cases = ["john", "JOHN", "John", "super", "SUPER", "Super"]

        for search_term in test_cases:
            request = rf.get("/contributors/", {"q": search_term})
            view = ContributorListView()
            view.setup(request)

            queryset = view.get_queryset()

            if search_term.lower() == "john":
                assert queryset.count() == 1
                assert contributor1 in queryset
            elif search_term.lower() == "super":
                assert queryset.count() == 1
                assert contributor2 in queryset

    def test_contributorlistview_search_partial_match(self, rf):
        # Create test contributors
        contributor1 = Contributor.objects.create(name="Alexander", address="addr1")
        contributor2 = Contributor.objects.create(name="Sandra", address="addr2")

        # Create social platform
        github = SocialPlatform.objects.create(name="GitHub", prefix="g@")
        Handle.objects.create(
            contributor=contributor2, platform=github, handle="pythonista"
        )

        # Test partial searches
        request = rf.get("/contributors/", {"q": "alex"})
        view = ContributorListView()
        view.setup(request)
        queryset = view.get_queryset()

        assert queryset.count() == 1
        assert contributor1 in queryset

        request = rf.get("/contributors/", {"q": "thon"})
        view = ContributorListView()
        view.setup(request)
        queryset = view.get_queryset()

        assert queryset.count() == 1
        assert contributor2 in queryset

    def test_contributorlistview_no_search_query(self, rf):
        # Create test contributors
        Contributor.objects.create(name="User1", address="addr1")
        Contributor.objects.create(name="User2", address="addr2")
        Contributor.objects.create(name="User3", address="addr3")

        # Create request without search query
        request = rf.get("/contributors/")
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should return all contributors
        assert queryset.count() == 3

    def test_contributorlistview_empty_search_query(self, rf):
        # Create test contributors
        Contributor.objects.create(name="User1", address="addr1")
        Contributor.objects.create(name="User2", address="addr2")

        # Create request with empty search query
        request = rf.get("/contributors/", {"q": ""})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should return all contributors
        assert queryset.count() == 2

    def test_contributorlistview_search_no_results(self, rf):
        # Create test contributors
        Contributor.objects.create(name="Alice", address="addr1")
        Contributor.objects.create(name="Bob", address="addr2")

        # Create request with non-matching search query
        request = rf.get("/contributors/", {"q": "xyz123"})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should return empty queryset
        assert queryset.count() == 0

    def test_contributorlistview_search_context_data(self, rf):
        # Create a contributor
        Contributor.objects.create(name="Test User", address="addr1")

        # Create request with search query
        request = rf.get("/contributors/", {"q": "test"})
        view = ContributorListView()
        view.setup(request)
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        # Should include search query in context
        assert "search_query" in context
        assert context["search_query"] == "test"

    def test_contributorlistview_search_context_no_query(self, rf):
        # Create a contributor
        Contributor.objects.create(name="Test User", address="addr1")

        # Create request without search query
        request = rf.get("/contributors/")
        view = ContributorListView()
        view.setup(request)
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        # Should include empty search query in context
        assert "search_query" in context
        assert context["search_query"] == ""

    def test_contributorlistview_search_duplicate_handles(self, rf):
        # Create test contributors
        contributor1 = Contributor.objects.create(name="User1", address="addr1")
        contributor2 = Contributor.objects.create(name="User2", address="addr2")

        # Create social platform
        platform = SocialPlatform.objects.create(name="Platformxs", prefix="xs")

        # Create handles with similar names
        Handle.objects.create(
            contributor=contributor1, platform=platform, handle="developer1"
        )
        Handle.objects.create(
            contributor=contributor2, platform=platform, handle="developer2"
        )

        # Create request with search query
        request = rf.get("/contributors/", {"q": "developer"})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should find both contributors (distinct results)
        assert queryset.count() == 2
        assert contributor1 in queryset
        assert contributor2 in queryset

    def test_contributorlistview_search_multiple_handles_same_contributor(self, rf):
        # Create test contributor
        contributor = Contributor.objects.create(name="Test User", address="addr1")

        # Create social platforms
        github = SocialPlatform.objects.create(name="GitHub", prefix="g@")
        discord = SocialPlatform.objects.create(name="Discord", prefix="")

        # Create multiple handles for same contributor
        Handle.objects.create(
            contributor=contributor, platform=github, handle="python_dev"
        )
        Handle.objects.create(
            contributor=contributor, platform=discord, handle="python_lover"
        )

        # Create request with search query
        request = rf.get("/contributors/", {"q": "python"})
        view = ContributorListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should find contributor only once (distinct results)
        assert queryset.count() == 1
        assert contributor in queryset

    def test_contributorlistview_integration_search(self, client):
        # Create test data
        contributor1 = Contributor.objects.create(
            name="Alice Developer", address="addr1"
        )
        contributor2 = Contributor.objects.create(name="Bob Tester", address="addr2")

        github = SocialPlatform.objects.create(name="GitHub", prefix="g@")
        Handle.objects.create(
            contributor=contributor1, platform=github, handle="alice_codes"
        )

        # Test search by name
        response = client.get(reverse("contributors"), {"q": "alice"})

        assert response.status_code == 200
        assert "search_query" in response.context
        assert response.context["search_query"] == "alice"
        assert contributor1 in response.context["contributor_list"]
        assert contributor2 not in response.context["contributor_list"]

        # Test search by handle
        response = client.get(reverse("contributors"), {"q": "codes"})

        assert response.status_code == 200
        assert contributor1 in response.context["contributor_list"]
        assert contributor2 not in response.context["contributor_list"]

        # Test no results
        response = client.get(reverse("contributors"), {"q": "nonexistent"})

        assert response.status_code == 200
        assert len(response.context["contributor_list"]) == 0


class TestContributorDetailView:
    """Testing class for :class:`core.views.ContributorDetailView`."""

    def test_contributordetailview_is_subclass_of_detailview(self):
        assert issubclass(ContributorDetailView, DetailView)

    def test_contributordetailview_model(self):
        view = ContributorDetailView()
        assert view.model == Contributor


@pytest.mark.django_db
class TestDbContributorDetailView:
    """Testing class for :class:`core.views.ContributorDetailView` with database."""

    def test_contributordetailview_get_object(self, rf):
        contributor = Contributor.objects.create(
            name="test_contributor", address="test_address"
        )
        request = rf.get(f"/contributors/{contributor.id}/")

        view = ContributorDetailView()
        view.setup(request, pk=contributor.id)

        obj = view.get_object()

        assert obj == contributor
        assert obj.name == "test_contributor"


class TestCycleListView:
    """Testing class for :class:`core.views.CycleListView`."""

    def test_cyclelistview_is_subclass_of_listview(self):
        assert issubclass(CycleListView, ListView)

    def test_cyclelistview_model(self):
        view = CycleListView()
        assert view.model == Cycle

    def test_cyclelistview_paginate_by(self):
        view = CycleListView()
        assert view.paginate_by == 10


@pytest.mark.django_db
class TestDbCycleListView:
    """Testing class for :class:`core.views.CycleListView` with database."""

    def test_cyclelistview_get_queryset(self, rf):
        request = rf.get("/cycles/")

        # Create test cycles
        cycle1 = Cycle.objects.create(start="2023-01-01", end="2023-01-31")
        cycle2 = Cycle.objects.create(start="2023-02-01", end="2023-02-28")

        view = CycleListView()
        view.setup(request)

        queryset = view.get_queryset()

        # Should be in reverse order (most recent first)
        assert queryset.count() == 2
        assert queryset.first() == cycle2  # Most recent
        assert queryset.last() == cycle1  # Oldest


class TestCycleDetailView:
    """Testing class for :class:`core.views.CycleDetailView`."""

    def test_cycledetailview_is_subclass_of_detailview(self):
        assert issubclass(CycleDetailView, DetailView)

    def test_cycledetailview_model(self):
        view = CycleDetailView()
        assert view.model == Cycle


class TestIssueListView:
    """Testing class for :class:`core.views.IssueListView`."""

    def test_issuelistview_is_subclass_of_listview(self):
        assert issubclass(IssueListView, ListView)

    def test_issuelistview_model(self):
        view = IssueListView()
        assert view.model == Issue

    def test_issuelistview_paginate_by(self):
        view = IssueListView()
        assert view.paginate_by == 20


@pytest.mark.django_db
class TestDbIssueListView:
    """Testing class for :class:`core.views.IssueListView` with database."""

    def test_issuelistview_get_queryset(self, rf):
        request = rf.get("/issues/")

        # Create test issues
        issue1 = Issue.objects.create(number=5055)
        issue2 = Issue.objects.create(number=5050)
        Issue.objects.create(number=5051)
        Issue.objects.create(number=5052, status=IssueStatus.WONTFIX)
        Issue.objects.create(number=5053, status=IssueStatus.ADDRESSED)
        Issue.objects.create(number=5054, status=IssueStatus.ARCHIVED)

        view = IssueListView()
        view.setup(request)

        queryset = view.get_queryset()

        assert queryset.count() == 3
        assert queryset.first() == issue2
        assert queryset.last() == issue1


@pytest.mark.django_db
class TestDbCycleDetailView:
    """Testing class for :class:`core.views.CycleDetailView` with database."""

    def test_cycledetailview_get_object(self, rf):
        cycle = Cycle.objects.create(start="2023-01-01", end="2023-01-31")
        request = rf.get(f"/cycles/{cycle.id}/")

        view = CycleDetailView()
        view.setup(request, pk=cycle.id)

        obj = view.get_object()

        assert obj == cycle
        assert obj.start.strftime("%Y-%m-%d") == "2023-01-01"


class TestIssueDetailView:
    """Test case for IssueDetailView."""

    def test_issuedetailview_is_subclass_of_detailview(self):
        assert issubclass(IssueDetailView, DetailView)

    def test_issuedetailview_model(self):
        view = IssueDetailView()
        assert view.model == Issue


@pytest.mark.django_db
class TestDbIssueDetailView:
    """Testing class for :class:`core.views.IssueDetailView` with database."""

    def test_issuedetailview_get_object(self, rf, issue):
        request = rf.get(f"/issues/{issue.id}/")

        view = IssueDetailView()
        view.setup(request, pk=issue.id)

        obj = view.get_object()

        assert obj == issue
        # Use the correct field name from your Issue model
        assert obj.number == issue.number  # Changed from issue_number to number

    def test_issuedetailview_accessible_to_regular_user(
        self, client, regular_user, issue
    ):
        """Test that regular users can access the view."""
        client.force_login(regular_user)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_issuedetailview_accessible_to_superuser(self, client, superuser, issue):
        """Test that superusers can access the view."""
        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_issuedetailview_github_data_added_for_superuser(
        self, client, superuser, issue, mocker
    ):
        """Test that GitHub data is added to context for superusers."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        # Create datetime objects for testing
        created_at = datetime(2023, 1, 1, 0, 0, 0)
        updated_at = datetime(2023, 1, 2, 0, 0, 0)

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": created_at,  # Use datetime object
                "updated_at": updated_at,  # Use datetime object
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "github_issue" in response.context
        assert response.context["issue_title"] == "Test Issue"
        assert response.context["issue_created_at"] == created_at
        assert response.context["issue_updated_at"] == updated_at
        mock_get_issue.assert_called_once_with(superuser, issue.number)

    def test_issuedetailview_no_github_data_for_regular_user(
        self, client, regular_user, issue, mocker
    ):
        """Test that GitHub data is NOT added to context for regular users."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        client.force_login(regular_user)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        # Regular users should not have GitHub context data
        assert "issue_html_url" in response.context
        assert "github_issue" not in response.context
        assert "issue_title" not in response.context
        # GitHub API should not be called for regular users
        mock_get_issue.assert_not_called()

    def test_issuedetailview_github_error_for_superuser(
        self, client, superuser, issue, mocker
    ):
        """Test that GitHub errors are handled for superusers."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {"success": False, "error": "Authentication failed"}
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["github_error"] == "Authentication failed"
        assert "github_issue" not in response.context

    def test_issuedetailview_same_template_used_for_all_users(
        self, client, regular_user, superuser, issue
    ):
        """Test that the same template is used for both user types."""
        client.force_login(regular_user)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response_regular = client.get(url)

        client.force_login(superuser)
        response_super = client.get(url)

        # Both should use the same template
        regular_templates = [t.name for t in response_regular.templates]
        super_templates = [t.name for t in response_super.templates]

        assert "core/issue_detail.html" in regular_templates
        assert "core/issue_detail.html" in super_templates

    def test_issuedetailview_github_api_called_with_correct_arguments(
        self, client, superuser, issue, mocker
    ):
        """Test that GitHub API is called with correct user and issue number."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": [],
                "assignees": [],
                "html_url": "",
                "created_at": "",
                "updated_at": "",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        # Verify the function was called with correct arguments
        mock_get_issue.assert_called_once_with(superuser, issue.number)

    def test_issuedetailview_context_data_includes_all_github_fields(
        self, client, superuser, issue, mocker
    ):
        """Test that all GitHub fields are included in context when successful."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Complete Test Issue",
                "body": "Complete test body with **markdown**",
                "state": "closed",
                "labels": ["bug", "feature", "urgent"],
                "assignees": ["user1", "user2", "user3"],
                "html_url": "https://github.com/asastats/rewards-site/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        context = response.context

        # Check all GitHub-related context variables
        assert context["github_issue"] == mock_github_data["issue"]
        assert context["issue_title"] == "Complete Test Issue"
        assert context["issue_body"] == "Complete test body with **markdown**"
        assert context["issue_state"] == "closed"
        assert context["issue_labels"] == ["bug", "feature", "urgent"]
        assert context["issue_assignees"] == ["user1", "user2", "user3"]
        assert (
            context["issue_html_url"]
            == "https://github.com/asastats/rewards-site/issues/123"
        )
        assert context["issue_created_at"] == "2023-01-01T10:00:00"
        assert context["issue_updated_at"] == "2023-01-15T15:30:00"


@pytest.mark.django_db
class TestIssueDetailViewWithForm:
    """Test the IssueDetailView with the new form functionality."""

    def test_issuedetailview_labels_form_in_context_for_superuser_and_open_issue(
        self, client, superuser, issue, mocker
    ):
        """Test that labels form is in context for superusers when GitHub issue is open."""
        # Mock GitHub issue as open
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",  # Issue is open
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "labels_form" in response.context
        assert isinstance(response.context["labels_form"], IssueLabelsForm)

    def test_issuedetailview_labels_form_not_in_context_for_superuser_and_closed_issue(
        self, client, superuser, issue, mocker
    ):
        """Test that labels form is NOT in context for superusers when GitHub issue is closed."""
        # Mock GitHub issue as closed
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "closed",  # Issue is closed
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "labels_form" not in response.context

    def test_issuedetailview_labels_form_not_in_context_for_regular_user(
        self, client, regular_user, issue, mocker
    ):
        """Test that labels form is NOT in context for regular users even if issue is open."""
        # Mock GitHub issue as open
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",  # Issue is open
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(regular_user)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "labels_form" not in response.context

    def test_issuedetailview_labels_form_not_in_context_when_github_fails(
        self, client, superuser, issue, mocker
    ):
        """Test that labels form is NOT in context when GitHub data fetch fails."""
        # Mock GitHub issue fetch failure
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {"success": False, "error": "GitHub API error"}
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "labels_form" not in response.context
        assert "github_error" in response.context

    def test_issuedetailview_form_prepopulated_with_existing_labels(
        self, client, superuser, issue, mocker
    ):
        """Test that form is prepopulated with existing GitHub labels."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        # Mock GitHub issue with existing labels including priority
        # Use only labels that exist in ISSUE_CREATION_LABEL_CHOICES
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": [
                    "bug",
                    "feature",
                    "high priority",
                    "question",
                ],  # Only valid choices
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        form = response.context["labels_form"]

        # Check that form is prepopulated with correct values
        # Only labels that exist in ISSUE_CREATION_LABEL_CHOICES should be included
        assert set(form.initial["labels"]) == {"bug", "feature"}
        assert form.initial["priority"] == "high priority"

    def test_issuedetailview_form_prepopulated_with_default_priority_when_no_priority(
        self, client, superuser, issue, mocker
    ):
        """Test that form uses default priority when no priority label exists."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        # Mock GitHub issue with labels but no priority
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "feature"],  # No priority label, only valid choices
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        form = response.context["labels_form"]

        # Check that form uses default priority
        assert set(form.initial["labels"]) == {"bug", "feature"}
        assert form.initial["priority"] == "medium priority"  # Default

    def test_issuedetailview_form_prepopulated_with_unknown_labels_filtered_out(
        self, client, superuser, issue, mocker
    ):
        """Test that unknown labels are filtered out during prepopulation."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        # Mock GitHub issue with some unknown labels
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "unknown_label", "high priority", "another_unknown"],
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        form = response.context["labels_form"]

        # Check that only known labels are included
        assert form.initial["labels"] == ["bug"]  # Only known label
        assert form.initial["priority"] == "high priority"

    def test_issuedetailview_priority_detection_with_various_formats(
        self, client, superuser, issue, mocker
    ):
        """Test that priority detection works with various label formats."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        # Mock GitHub issue with different priority label formats
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": [
                    "bug",
                    "low priority",  # Use lowercase to match actual priority choices
                ],  # Only one priority to avoid ambiguity
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        form = response.context["labels_form"]

        # Should detect the priority label correctly
        assert form.initial["labels"] == ["bug"]
        assert form.initial["priority"] == "low priority"

    def test_issuedetailview_post_request_sets_labels_successfully(
        self, client, superuser, issue, mocker
    ):
        """Test that POST request successfully sets labels on GitHub issue."""
        # Mock the set_labels_to_issue function
        mock_add_labels = mocker.patch("core.views.set_labels_to_issue")
        mock_add_labels.return_value = {
            "success": True,
            "message": (
                "Added labels ['bug', 'feature', 'high priority'] "
                f"to issue #{issue.number}"
            ),
            "current_labels": ["bug", "feature", "high priority"],
        }

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        # Submit form with selected labels and priority
        response = client.post(
            url, {"labels": ["bug", "feature"], "priority": "high priority"}
        )

        assert response.status_code == 302  # Redirect after POST
        # Fix the URL assertion to match your actual URL pattern
        expected_url = reverse("issue-detail", kwargs={"pk": issue.pk})
        assert response.url == expected_url

    def test_issuedetailview_post_request_handles_github_error(
        self, client, superuser, issue, mocker
    ):
        """Test that GitHub errors are handled when setting labels."""
        # Mock the set_labels_to_issue function to return error
        mock_add_labels = mocker.patch("core.views.set_labels_to_issue")
        mock_add_labels.return_value = {
            "success": False,
            "error": "GitHub API rate limit exceeded",
        }

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(url, {"labels": ["bug"], "priority": "medium priority"})

        assert response.status_code == 302

    def test_issuedetailview_post_request_invalid_form(self, client, superuser, issue):
        """Test that invalid form submission shows error."""
        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        # Submit empty form (invalid)
        response = client.post(url, {})

        assert response.status_code == 302

    def test_issuedetailview_post_request_denied_for_regular_user(
        self, client, regular_user, issue
    ):
        """Test that regular users cannot submit the form."""
        client.force_login(regular_user)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(url, {"labels": ["bug"], "priority": "medium priority"})

        # Should redirect with error message
        assert response.status_code == 302

    def test_issuedetailview_context_variables_for_priority_and_labels(
        self, client, superuser, issue, mocker
    ):
        """Test that context variables for current priority and labels are set."""
        # Mock the issue_by_number function
        mock_get_issue = mocker.patch("core.views.issue_by_number")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "feature", "high priority"],  # Use valid choices
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        context = response.context

        # Check that context variables are set
        assert context["current_priority"] == "high priority"
        assert set(context["current_custom_labels"]) == {"bug", "feature"}

    def test_issuedetailview_form_in_template_for_superuser(
        self, client, superuser, issue, mocker
    ):
        """Test that form appears in template for superusers."""
        # Mock GitHub data
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "high priority"],
                "assignees": ["user1"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        # Check that form elements are in the response
        content = response.content.decode()
        assert "Set labels" in content  # Button text
        assert "bug" in content  # Label option
        assert "high priority" in content  # Priority option


@pytest.mark.django_db
class TestIssueDetailViewSubmissionHandlers:
    """Test the submission handler methods in IssueDetailView."""

    # Tests for _handle_labels_submission
    def test_issuedetailview_handle_labels_submission_success(
        self, client, superuser, issue, mocker
    ):
        """Test successful labels form submission."""
        # Mock the set_labels_to_issue function from utils.issues
        mock_add_labels = mocker.patch("core.views.set_labels_to_issue")
        mock_add_labels.return_value = {
            "success": True,
            "message": f"Added labels ['bug', 'feature', 'high priority'] to issue #{issue.number}",
            "current_labels": ["bug", "feature", "high priority"],
        }

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "labels": ["bug", "feature"],
                "priority": "high priority",
                "submit_labels": "Set labels",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Verify the function was called with correct arguments
        mock_add_labels.assert_called_once_with(
            superuser, issue.number, ["bug", "feature", "high priority"]
        )

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            f"Successfully set labels for issue #{issue.number}" in str(message)
            for message in messages
        )

    def test_issuedetailview_handle_labels_submission_github_failure(
        self, client, superuser, issue, mocker
    ):
        """Test labels form submission when GitHub operation fails."""
        # Mock the set_labels_to_issue function to return failure
        mock_add_labels = mocker.patch("core.views.set_labels_to_issue")
        mock_add_labels.return_value = {
            "success": False,
            "error": "GitHub API rate limit exceeded",
        }

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "labels": ["bug"],
                "priority": "medium priority",
                "submit_labels": "Set labels",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Failed to set labels" in str(message) for message in messages)
        assert any(
            "GitHub API rate limit exceeded" in str(message) for message in messages
        )

    def test_issuedetailview_handle_labels_submission_invalid_form(
        self, client, superuser, issue
    ):
        """Test labels form submission with invalid form data."""
        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        # Submit empty form (invalid - required fields missing)
        response = client.post(
            url,
            {
                "submit_labels": "Set labels"
                # Missing 'labels' and 'priority' fields
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Please correct the errors in the form" in str(message)
            for message in messages
        )

    def test_issuedetailview_handle_labels_submission_empty_labels(
        self, client, superuser, issue
    ):
        """Test labels form submission with empty labels list."""
        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        # Submit form with empty labels (invalid)
        response = client.post(
            url,
            {
                "labels": [],  # Empty labels
                "priority": "medium priority",
                "submit_labels": "Set labels",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Please correct the errors in the form" in str(message)
            for message in messages
        )

    # Tests for _handle_close_submission - addressed action
    def test_issuedetailview_handle_close_submission_addressed_success(
        self, client, superuser, issue, mocker
    ):
        """Test successful close as addressed submission."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "work in progress", "feature"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "This issue has been addressed successfully.",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check that issue status was updated
        issue.refresh_from_db()
        assert issue.status == IssueStatus.ADDRESSED

        # Check that close_issue_with_labels was called with correct arguments
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        assert call_args["user"] == superuser
        assert call_args["issue_number"] == issue.number
        assert call_args["comment"] == "This issue has been addressed successfully."
        assert "addressed" in call_args["labels_to_set"]
        assert "work in progress" not in call_args["labels_to_set"]
        assert "bug" in call_args["labels_to_set"]
        assert "feature" in call_args["labels_to_set"]

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            f"Issue #{issue.number} closed as addressed successfully" in str(message)
            for message in messages
        )

    def test_issuedetailview_handle_close_submission_addressed_success_no_comment(
        self, client, superuser, issue, contribution, mocker
    ):
        """Test successful close as addressed submission without comment."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")
        mock_add_reaction = mocker.patch("core.views.add_reaction_to_message")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        contribution.issue = issue
        contribution.save()
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",  # Empty comment
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302

        # Check that close_issue_with_labels was called with empty comment
        mock_close_issue.assert_called_once()
        mock_add_reaction.assert_called_once_with(
            contribution.url, DISCORD_EMOJIS.get("addressed")
        )

        call_args = mock_close_issue.call_args[1]
        assert call_args["comment"] == ""

    def test_issuedetailview_handle_close_submission_wontfix_success(
        self, client, superuser, issue, mocker
    ):
        """Test successful close as wontfix submission."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "work in progress"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "wontfix",
                "close_comment": "This issue will not be fixed.",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check that issue status was updated
        issue.refresh_from_db()
        assert issue.status == IssueStatus.WONTFIX

        # Check that close_issue_with_labels was called with correct arguments
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        assert call_args["user"] == superuser
        assert call_args["issue_number"] == issue.number
        assert call_args["comment"] == "This issue will not be fixed."
        assert "wontfix" in call_args["labels_to_set"]
        assert "work in progress" not in call_args["labels_to_set"]

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            f"Issue #{issue.number} closed as wontfix successfully" in str(message)
            for message in messages
        )

    def test_issuedetailview_handle_close_submission_invalid_action(
        self, client, superuser, issue
    ):
        """Test close submission with invalid action."""
        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "invalid_action",  # Invalid action
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Invalid close action" in str(message) for message in messages)

    def test_issuedetailview_handle_close_submission_github_fetch_failure(
        self, client, superuser, issue, mocker
    ):
        """Test close submission when GitHub issue fetch fails."""
        # Mock GitHub issue fetch failure
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {"success": False, "error": "Authentication failed"}
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Failed to fetch GitHub issue" in str(message) for message in messages
        )
        assert any("Authentication failed" in str(message) for message in messages)

    def test_issuedetailview_handle_close_submission_already_closed_issue(
        self, client, superuser, issue, mocker
    ):
        """Test close submission when GitHub issue is already closed."""
        # Mock GitHub issue as closed
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "closed",  # Already closed
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("already closed on GitHub" in str(message) for message in messages)

    def test_issuedetailview_handle_close_submission_github_close_failure(
        self, client, superuser, issue, mocker
    ):
        """Test close submission when GitHub close operation fails."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {
            "success": False,
            "error": "Failed to close issue on GitHub",
        }

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check that local status was reverted
        issue.refresh_from_db()
        assert issue.status == IssueStatus.CREATED  # Reverted to original

        # Check error message - the actual error message from the view
        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Failed to close issue on GitHub" in str(message) for message in messages
        )

    def test_issuedetailview_handle_close_submission_exception_handling(
        self, client, superuser, issue, mocker
    ):
        """Test close submission when an unexpected exception occurs."""
        # Mock GitHub function to raise an exception
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_get_issue.side_effect = Exception("Unexpected error")

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Error closing issue" in str(message) for message in messages)
        assert any("Unexpected error" in str(message) for message in messages)

    def test_issuedetailview_handle_close_submission_labels_processing(
        self, client, superuser, issue, mocker
    ):
        """Test that labels are properly processed (remove work in progress, add correct label)."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": [
                    "work in progress",
                    "bug",
                    "enhancement",
                    "WORK IN PROGRESS",
                ],  # Multiple cases
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302

        # Check that close_issue_with_labels was called with correct labels
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        labels_to_set = call_args["labels_to_set"]

        # Should contain addressed label and other labels except work in progress variants
        assert "addressed" in labels_to_set
        assert "bug" in labels_to_set
        assert "enhancement" in labels_to_set
        assert "work in progress" not in labels_to_set
        assert "WORK IN PROGRESS" not in labels_to_set

    def test_issuedetailview_handle_close_submission_existing_label_not_duplicated(
        self, client, superuser, issue, mocker
    ):
        """Test that existing addressed/wontfix label is not duplicated."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "addressed"],  # Already has addressed label
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302

        # Check that close_issue_with_labels was called with labels
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        labels_to_set = call_args["labels_to_set"]

        # Should contain only one 'addressed' label (not duplicated)
        assert labels_to_set.count("addressed") == 1


@pytest.mark.django_db
class TestIssueDetailViewCloseFunctionality:
    """Test the close issue functionality in IssueDetailView."""

    def test_issuedetailview_close_buttons_not_shown_for_regular_user(
        self, client, regular_user, issue, mocker
    ):
        """Test that close buttons are not shown for regular users."""
        # Mock GitHub issue as open
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(regular_user)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Close as addressed" not in content
        assert "Close as wontfix" not in content

    def test_issuedetailview_close_buttons_not_shown_for_closed_issue(
        self, client, superuser, issue, mocker
    ):
        """Test that close buttons are not shown for closed GitHub issues."""
        # Mock GitHub issue as closed
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "closed",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Close as addressed" not in content
        assert "Close as wontfix" not in content

    def test_issuedetailview_close_buttons_shown_for_open_issue_and_superuser(
        self, client, superuser, issue, mocker
    ):
        """Test that close buttons are shown for open issues and superusers."""
        # Mock GitHub issue as open
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Close as addressed" in content
        assert "Close as wontfix" in content

    def test_issuedetailview_close_as_addressed_success(
        self, client, superuser, issue, mocker
    ):
        """Test successful close as addressed action."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "work in progress"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "Fixed the issue",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check that issue status was updated
        issue.refresh_from_db()
        assert issue.status == IssueStatus.ADDRESSED

        # Check that close_issue_with_labels was called with correct arguments
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        assert call_args["user"] == superuser
        assert call_args["issue_number"] == issue.number
        assert call_args["comment"] == "Fixed the issue"
        assert "addressed" in call_args["labels_to_set"]
        assert "work in progress" not in call_args["labels_to_set"]

    def test_issuedetailview_close_as_wontfix_success(
        self, client, superuser, issue, mocker
    ):
        """Test successful close as wontfix action."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "work in progress"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "wontfix",
                "close_comment": "Will not fix",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check that issue status was updated
        issue.refresh_from_db()
        assert issue.status == IssueStatus.WONTFIX

        # Check that close_issue_with_labels was called with correct arguments
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        assert call_args["user"] == superuser
        assert call_args["issue_number"] == issue.number
        assert call_args["comment"] == "Will not fix"
        assert "wontfix" in call_args["labels_to_set"]
        assert "work in progress" not in call_args["labels_to_set"]

    def test_issuedetailview_close_as_wontfix_success_existing_label(
        self, client, superuser, issue, mocker
    ):
        """Test successful close as wontfix action."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug", "work in progress", "wontfix"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "wontfix",
                "close_comment": "Will not fix",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("issue-detail", kwargs={"pk": issue.pk})

        # Check that issue status was updated
        issue.refresh_from_db()
        assert issue.status == IssueStatus.WONTFIX

        # Check that close_issue_with_labels was called with correct arguments
        mock_close_issue.assert_called_once()
        call_args = mock_close_issue.call_args[1]
        assert call_args["user"] == superuser
        assert call_args["issue_number"] == issue.number
        assert call_args["comment"] == "Will not fix"
        assert "wontfix" in call_args["labels_to_set"]
        assert "work in progress" not in call_args["labels_to_set"]

    def test_issuedetailview_close_issue_github_failure(
        self, client, superuser, issue, mocker
    ):
        """Test that local status is reverted when GitHub operation fails."""
        # Mock GitHub functions
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_close_issue = mocker.patch("core.views.close_issue_with_labels")

        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data
        mock_close_issue.return_value = {"success": False, "error": "GitHub API error"}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302

        # Check that issue status was reverted to original
        issue.refresh_from_db()
        assert issue.status == IssueStatus.CREATED  # Original status

    def test_issuedetailview_close_already_closed_issue(
        self, client, superuser, issue, mocker
    ):
        """Test closing an issue that is already closed on GitHub."""
        # Mock GitHub issue as closed
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "closed",  # Already closed
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "addressed",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302

        # Check messages for error
        messages = list(get_messages(response.wsgi_request))
        assert any("already closed" in str(message) for message in messages)

    def test_issuedetailview_close_issue_invalid_action(self, client, superuser, issue):
        """Test closing with invalid action."""
        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "close_action": "invalid_action",
                "close_comment": "",
                "submit_close": "Confirm Close",
            },
        )

        assert response.status_code == 302

        # Check messages for error
        messages = list(get_messages(response.wsgi_request))
        assert any("Invalid close action" in str(message) for message in messages)

    def test_issuedetailview_labels_form_not_shown_for_closed_issue(
        self, client, superuser, issue, mocker
    ):
        """Test that labels form is not shown for closed GitHub issues."""
        # Mock GitHub issue as closed
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "closed",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "labels_form" not in response.context

    def test_issuedetailview_labels_form_shown_for_open_issue(
        self, client, superuser, issue, mocker
    ):
        """Test that labels form is shown for open GitHub issues."""
        # Mock GitHub issue as open
        mock_get_issue = mocker.patch("core.views.issue_by_number")
        mock_github_data = {
            "success": True,
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-15T15:30:00",
            },
        }
        mock_get_issue.return_value = mock_github_data

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "labels_form" in response.context
        assert isinstance(response.context["labels_form"], IssueLabelsForm)


@pytest.mark.django_db
class TestDbCreateIssueView:
    """Testing class for :class:`core.views.CreateIssueView` with database."""

    def test_createissueview_get_stores_contribution_id(
        self, rf, superuser, contribution
    ):
        request = rf.get(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)

        response = view.get(request, contribution_id=contribution.id)

        assert view.contribution_id == contribution.id
        assert response.status_code == 200

    def test_createissueview_post_stores_contribution_id(
        self, rf, superuser, contribution
    ):
        request = rf.post(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)

        response = view.post(request, contribution_id=contribution.id)

        assert view.contribution_id == contribution.id
        assert response.status_code == 200

    def test_createissueview_get_success_url(self, rf, superuser, contribution):
        request = rf.get(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)
        view.contribution_id = contribution.id

        success_url = view.get_success_url()

        expected_url = reverse("contribution-detail", args=[contribution.id])
        assert success_url == expected_url

    def test_createissueview_get_initial_with_contribution_id(
        self, rf, superuser, contribution, mocker
    ):
        request = rf.get(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)
        view.contribution_id = contribution.id

        # Mock the issue_data_for_contribution function
        mock_issue_data = mocker.patch("core.views.issue_data_for_contribution")
        mock_issue_data.return_value = {
            "priority": "high priority",
            "issue_body": "Test body",
            "issue_title": "Test title",
            "labels": ["bug"],
        }

        initial = view.get_initial()

        assert "priority" in initial
        assert "issue_body" in initial
        assert "issue_title" in initial
        assert "labels" in initial

    def test_createissueview_get_initial_without_contribution_id(self, rf, superuser):
        request = rf.get("/create-issue/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request)
        view.contribution_id = None

        initial = view.get_initial()

        expected_data = {
            "priority": "medium priority",
            "issue_body": "Please provide issue description here.",
            "issue_title": "Issue title",
        }
        assert initial == expected_data

    def test_createissueview_get_context_data(
        self, rf, superuser, contribution, mocker
    ):
        request = rf.get(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)
        view.contribution_id = contribution.id
        view.object = None

        # Mock the info method
        mock_info = mocker.patch.object(Contribution, "info")
        mock_info.return_value = "Test Contribution Info"

        context = view.get_context_data()

        assert context["contribution_id"] == contribution.id
        assert context["contribution_info"] == "Test Contribution Info"
        assert "Create issue for Test Contribution Info" in context["page_title"]

    def test_createissueview_form_valid_success(
        self, rf, superuser, contribution, mocker
    ):
        request = rf.post(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)
        view.contribution_id = contribution.id

        # Mock external dependencies
        mock_create_github_issue = mocker.patch("core.views.create_github_issue")
        mock_create_github_issue.return_value = {"success": True, "issue_number": 123}

        mock_confirm_contribution = mocker.patch(
            "core.views.Issue.objects.confirm_contribution_with_issue"
        )
        mock_add_reaction = mocker.patch("core.views.add_reaction_to_message")

        # Create mock form with valid data
        mock_form = mocker.MagicMock()
        mock_form.cleaned_data = {
            "labels": ["bug", "feature"],
            "priority": "high priority",
            "issue_body": "Test issue body",
            "issue_title": "Test issue title",
        }

        response = view.form_valid(mock_form)

        # Verify GitHub issue creation was called with correct data
        mock_create_github_issue.assert_called_once_with(
            superuser,
            "Test issue title",
            "Test issue body",
            labels=["bug", "feature", "high priority"],
        )

        # Verify contribution was confirmed with issue
        mock_confirm_contribution.assert_called_once_with(123, contribution)

        # Verify Discord reaction was added
        mock_add_reaction.assert_called_once_with(contribution.url, mocker.ANY)

        # Verify response is successful
        assert response.status_code == 302

    def test_createissueview_form_valid_failure(
        self, rf, superuser, contribution, mocker
    ):
        request = rf.post(f"/create-issue/{contribution.id}/")
        request.user = superuser
        view = CreateIssueView()
        view.setup(request, contribution_id=contribution.id)
        view.contribution_id = contribution.id

        # Mock GitHub issue creation to fail
        mock_create_github_issue = mocker.patch("core.views.create_github_issue")
        mock_create_github_issue.return_value = {
            "success": False,
            "error": "GitHub API error",
        }

        # Create mock form with valid data
        mock_form = mocker.MagicMock()
        mock_form.cleaned_data = {
            "labels": ["bug"],
            "priority": "medium priority",
            "issue_body": "Test issue body",
            "issue_title": "Test issue title",
        }

        response = view.form_valid(mock_form)

        # Verify form error was added
        mock_form.add_error.assert_called_once_with(None, mocker.ANY)

        # Verify response indicates form is invalid
        assert response.status_code == 200

    def test_createissueview_requires_superuser(self, rf, regular_user, contribution):
        request = rf.get(f"/create-issue/{contribution.id}/")
        request.user = regular_user

        response = CreateIssueView.as_view()(request, contribution_id=contribution.id)

        # Should redirect to login or show permission denied
        assert response.status_code in [302, 403]

    def test_createissueview_superuser_access_granted(
        self, rf, superuser, contribution
    ):
        request = rf.get(f"/create-issue/{contribution.id}/")
        request.user = superuser

        response = CreateIssueView.as_view()(request, contribution_id=contribution.id)

        # Should return 200 for superuser
        assert response.status_code == 200


class EditProfilePageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="profilepage@testuser.com",
            username="profilepage",
        )
        self.user.set_password("12345o")
        self.user.save()
        self.client.login(username="profilepage", password="12345o")

    def post_invalid_input(self):
        return self.client.post(
            reverse("profile"),
            data=get_user_edit_fake_post_data(self.user, first_name="xyz" * 51),
        )

    def test_profile_page_uses_profile_template(self):
        response = self.client.get(reverse("profile"))
        self.assertTemplateUsed(response, "profile.html")

    def test_profile_page_passes_correct_user_to_template(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.context["form"].instance.username, self.user.username)

    def test_profile_page_displays_updateuserform_for_edit_user_data(self):
        response = self.client.get(reverse("profile"))
        self.assertIsInstance(response.context["form"], UpdateUserForm)
        self.assertContains(response, "first_name")

    def test_profile_page_displays_profileformset_for_edit_profile_data(self):
        response = self.client.get(reverse("profile"))
        self.assertIsInstance(response.context["profile_form"], ProfileFormSet)
        self.assertContains(response, "profile-0-github_token")

    def test_profile_page_post_ends_in_profile_page(self):
        response = self.client.post(
            reverse("profile"), data=get_user_edit_fake_post_data(self.user)
        )
        self.assertRedirects(response, reverse("profile"))

    def test_profile_page_saving_a_post_request_to_an_existing_user(self):
        self.client.post(
            reverse("profile"),
            data=get_user_edit_fake_post_data(
                self.user, first_name="Newname", last_name="Newlastname"
            ),
        )
        user = user_model.objects.last()
        self.assertEqual(user.first_name, "Newname")
        self.assertEqual(user.last_name, "Newlastname")

    def test_profile_page_edit_profile_for_invalid_input_nothing_saved_to_db(self):
        oldname = self.user.first_name
        self.post_invalid_input()
        self.assertEqual(oldname, self.user.first_name)

    def test_profile_page_for_invalid_input_renders_profile_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")

    def test_profile_page_edit_profile_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], UpdateUserForm)


class LoginPageTest(TestCase):
    def post_invalid_input(self):
        return self.client.post(
            reverse("account_login"), data={"login": "logn", "password": "12345"}
        )

    def test_login_page_renders_login_template(self):
        response = self.client.get(reverse("account_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_login_view_renders_loginform(self):
        response = self.client.get(reverse("account_login"))
        self.assertIsInstance(response.context["form"], LoginForm)

    def test_for_invalid_input_renders_login_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_login_page_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], LoginForm)

    def test_for_invalid_input_shows_errors_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(
            response, "The username and/or password you specified are not correct."
        )

    def test_login_page_links_to_forget_password_page(self):
        response = self.client.get(reverse("account_login"))
        self.assertContains(response, reverse("account_reset_password"))


class TestProfileDisplay:
    """Testing class for :class:`core.views.ProfileDisplay`."""

    def test_profiledisplay_is_subclass_of_detailview(self):
        assert issubclass(ProfileDisplay, DetailView)

    def test_profiledisplay_sets_template_name(self):
        assert ProfileDisplay.template_name == "profile.html"

    def test_profiledisplay_sets_model_to_user(self):
        assert ProfileDisplay.model == User


@pytest.mark.django_db
class TestDbProfileDisplayView(BaseUserCreatedView):
    def test_profiledisplay_get_returns_both_forms_by_the_context_data(self):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        # Run.
        view_object = view.get(self.request)

        # Check.
        assert isinstance(view_object.context_data["form"], UpdateUserForm)
        assert isinstance(view_object.context_data["profile_form"], ProfileFormSet)
        assert isinstance(view_object.context_data["form"].instance, user_model)
        assert isinstance(view_object.context_data["profile_form"].instance, user_model)

    def test_profiledisplay_get_form_fills_form_with_user_data(self):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        # Run.
        form = view.get_form()

        # Check.
        assert form.data["email"] == self.user.email


class TestProfileUpdate:
    """Testing class for :class:`core.views.ProfileUpdate`."""

    def test_profileupdate_is_subclass_of_updateview(self):
        assert issubclass(ProfileUpdate, UpdateView)

    def test_profileupdate_issubclass_of_singleobjectmixin(self):
        assert issubclass(ProfileUpdate, SingleObjectMixin)

    def test_profileupdate_sets_template_name(self):
        assert ProfileUpdate.template_name == "profile.html"

    def test_profileupdate_sets_model_to_user(self):
        assert ProfileUpdate.model == User

    def test_profileupdate_sets_form_class_to_updateuserform(self):
        assert ProfileUpdate.form_class == UpdateUserForm

    def test_profileupdate_sets_success_url_to_profile(self):
        assert ProfileUpdate.success_url == reverse_lazy("profile")


@pytest.mark.django_db
class TestDbProfileUpdateView(BaseUserCreatedView):
    def test_profileupdateview_get_object_sets_user(self):
        # Setup view
        view = ProfileUpdate()
        view = self.setup_view(view, self.request)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == self.user

    def test_profileupdateview_get_form_returns_updateuserform(self):
        # Setup view
        view = ProfileUpdate()
        view = self.setup_view(view, self.request)
        # view.object = self.user.profile

        # Run.
        view_form = view.get_form()

        # Check.
        assert isinstance(view_form, UpdateUserForm)
        assert view_form.instance == self.user


class TestProfileEditView:
    """Testing class for :class:`core.views.ProfileEditView`."""

    def test_profileeditview_is_subclass_of_view(self):
        assert issubclass(ProfileEditView, View)


@pytest.mark.django_db
class TestDbProfileEditView(BaseUserCreatedView):
    def test_profileeditview_get_instantiates_profiledisplay_view(self):
        # Setup view
        view = ProfileEditView()
        view = self.setup_view(view, self.request)

        # Run.
        view_method = view.get(self.request)

        # Check.
        assert isinstance(view_method.context_data["view"], ProfileDisplay)

    def test_profileeditview_post_instantiates_profileupdate_view(self):
        # Setup view
        view = ProfileEditView()
        data = get_user_edit_fake_post_data(self.user)
        view = self.setup_view(view, self.request)

        # Run.
        # form=form, profile_form=profile_form
        view_method = view.post(
            self.request,
            form=UpdateUserForm(instance=self.user, data=data),
        )
        # Check.
        assert isinstance(view_method.context_data["view"], ProfileUpdate)
