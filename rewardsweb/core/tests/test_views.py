"""Testing module for :py:mod:`core.views` module."""

import time
from datetime import datetime, timezone

import pytest
from allauth.account.forms import LoginForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from core.models import Contribution, Contributor, Cycle, Handle, Issue, SocialPlatform
from core.forms import ProfileFormSet, UpdateUserForm
from core.views import (
    ContributionDetailView,
    ContributionUpdateView,
    ContributorListView,
    ContributorDetailView,
    CreateIssueView,
    CycleListView,
    CycleDetailView,
    IndexView,
    IssueDetailView,
    ProfileDisplay,
    ProfileEditView,
    ProfileUpdate,
)

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


class TestContributionUpdateView:
    """Testing class for :class:`core.views.ContributionUpdateView`."""

    def test_contributionupdateview_is_subclass_of_updateview(self):
        assert issubclass(ContributionUpdateView, UpdateView)

    def test_contributionupdateview_model(self):
        view = ContributionUpdateView()
        assert view.model == Contribution

    def test_contributionupdateview_form_class(self):
        view = ContributionUpdateView()
        from core.forms import ContributionEditForm

        assert view.form_class == ContributionEditForm

    def test_contributionupdateview_template_name(self):
        view = ContributionUpdateView()
        assert view.template_name == "core/contribution_edit.html"


@pytest.mark.django_db
class TestDbContributionUpdateView:
    """Testing class for :class:`core.views.ContributionUpdateView` with database."""

    def test_contributionupdateview_get_success_url(self, rf, superuser, contribution):
        request = rf.get(f"/contributions/{contribution.id}/edit/")
        request.user = superuser

        # Setup messages framework
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        view = ContributionUpdateView()
        view.setup(request, pk=contribution.id)
        view.object = contribution
        view.request = request

        success_url = view.get_success_url()

        expected_url = reverse("contribution-detail", kwargs={"pk": contribution.pk})
        assert success_url == expected_url

    def test_contributionupdateview_requires_superuser(
        self, rf, regular_user, contribution
    ):
        request = rf.get(f"/contributions/{contribution.id}/edit/")
        request.user = regular_user

        response = ContributionUpdateView.as_view()(request, pk=contribution.id)

        # Should redirect to login (302) for non-superusers
        assert response.status_code == 302

    def test_contributionupdateview_superuser_access_granted(
        self, rf, superuser, contribution
    ):
        request = rf.get(f"/contributions/{contribution.id}/edit/")
        request.user = superuser

        response = ContributionUpdateView.as_view()(request, pk=contribution.id)

        # Should return 200 for superuser
        assert response.status_code == 200


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
