"""Testing module for rewards app's views."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from core.models import Contributor
from rewards.views import AddAllocationsView, ClaimView, ReclaimAllocationsView

User = get_user_model()


class TestRewardsViews:
    """Test suite for ActiveNetworkAPIView."""

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture
    def user(self, db):
        """Create a normal authenticated user."""
        return User.objects.create_user(username="testuser", password="pass123")

    @pytest.fixture
    def superuser(self, db):
        """Create a superuser."""
        return User.objects.create_superuser(username="admin", password="pass123")

    # # ClaimView
    @pytest.mark.django_db
    def test_claimview_requires_login(self, rf):
        request = rf.get(reverse("claim"))
        request.user = AnonymousUser()

        response = ClaimView.as_view()(request)

        # Redirects to login page
        assert response.status_code == 302
        assert "/login" in response.url.lower()

    @pytest.mark.django_db
    def test_claimview_context_claimable_true(self, rf, user, mocker):
        """User has contributor address → claimable=True"""

        contributor = Contributor.objects.create(
            name="claimview", address="SOMEADDRESS"
        )
        user.profile.contributor = contributor

        request = rf.get(reverse("claim"))
        request.user = user

        response = ClaimView.as_view()(request)
        context = response.context_data

        assert context["claimable"] is True

    @pytest.mark.django_db
    def test_claimview_context_claimable_false_no_contributor(self, rf, user):
        """User has no contributor → claimable=False"""

        request = rf.get(reverse("claim"))
        request.user = user

        response = ClaimView.as_view()(request)
        context = response.context_data

        assert context["claimable"] is False

    # # AddAllocationsView
    @pytest.mark.django_db
    def test_addallocationsview_requires_login(self, rf, mocker):
        """Ensure the view redirects anonymous users to login page."""
        mocker.patch("rewards.views.is_admin_account_configured")
        mocker.patch(
            (
                "rewards.views.Contribution.objects."
                "addressed_contributions_addresses_and_amounts"
            ),
            return_value=(["ADDR1", "ADDR2"], [10, 20]),
        )
        request = rf.get(reverse("add_allocations"))
        request.user = AnonymousUser()

        response = AddAllocationsView.as_view()(request)

        assert response.status_code == 302  # redirect
        assert "/login" in response.url.lower()

    @pytest.mark.django_db
    def test_addallocationsview_superuser_can_access(self, rf, superuser, mocker):
        """Superusers should be able to access the page."""
        mocker.patch("rewards.views.is_admin_account_configured")
        mocker.patch(
            (
                "rewards.views.Contribution.objects."
                "addressed_contributions_addresses_and_amounts"
            ),
            return_value=(["ADDR1", "ADDR2"], [10, 20]),
        )
        request = rf.get(reverse("add_allocations"))
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        assert response.status_code == 200
        assert response.template_name == ["rewards/add_allocations.html"]

    @pytest.mark.django_db
    def test_addallocationsview_context_contains_allocations(
        self, rf, superuser, mocker
    ):
        """Ensure allocations from queryset are added to context."""

        # Mock database call
        mocked_contribs = mocker.patch(
            (
                "rewards.views.Contribution.objects."
                "addressed_contributions_addresses_and_amounts"
            ),
            return_value=(["ADDR1", "ADDR2"], [10, 20]),
        )
        mocker.patch("rewards.views.is_admin_account_configured")
        request = rf.get(reverse("add_allocations"))
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        context = response.context_data

        assert list(context["allocations"]) == [("ADDR1", 10), ("ADDR2", 20)]
        # Ensures function was called exactly once
        mocked_contribs.assert_called_once_with()

    @pytest.mark.django_db
    def test_addallocationsview_context_contains_use_admin_account(
        self, rf, superuser, mocker
    ):
        """Ensure allocations from queryset are added to context."""
        mocker.patch(
            (
                "rewards.views.Contribution.objects."
                "addressed_contributions_addresses_and_amounts"
            ),
            return_value=(["ADDR1", "ADDR2"], [10, 20]),
        )
        mocked_admin = mocker.patch("rewards.views.is_admin_account_configured")

        request = rf.get(reverse("add_allocations"))
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        context = response.context_data

        assert context["use_admin_account"] == mocked_admin.return_value
        # Ensures function was called exactly once
        mocked_admin.assert_called_once_with()

    @pytest.mark.django_db
    def test_addallocationsview_context_for_no_allocations(self, rf, superuser, mocker):
        """Ensure allocations from queryset are added to context."""

        # Mock database call
        mocker.patch(
            (
                "rewards.views.Contribution.objects."
                "addressed_contributions_addresses_and_amounts"
            ),
            return_value=([], []),
        )
        mocker.patch("rewards.views.is_admin_account_configured")
        request = rf.get(reverse("add_allocations"))
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        context = response.context_data

        assert "allocations" not in context
        assert "use_admin_account" not in context

    @pytest.mark.django_db
    def test_addallocationsview_normal_user_blocked(self, rf, user):
        """Non-superusers should NOT be allowed to access the page."""
        request = rf.get(reverse("add_allocations"))
        request.user = user

        response = AddAllocationsView.as_view()(request)

        # LoginRequiredMixin lets login first, so user gets 302 to login
        assert response.status_code in (302, 403)

    # # ReclaimAllocationsView
    @pytest.mark.django_db
    def test_reclaimallocationsview_requires_login(self, rf):
        request = rf.get(reverse("reclaim_allocations"))
        request.user = AnonymousUser()

        response = ReclaimAllocationsView.as_view()(request)

        assert response.status_code == 302
        assert "/login" in response.url.lower()

    @pytest.mark.django_db
    def test_reclaimallocationsview_superuser_can_access(self, rf, superuser, mocker):
        mocker.patch("rewards.views.is_admin_account_configured")
        mocker.patch("rewards.views.reclaimable_addresses")
        request = rf.get(reverse("reclaim_allocations"))
        request.user = superuser

        response = ReclaimAllocationsView.as_view()(request)

        assert response.status_code == 200
        assert response.template_name == ["rewards/reclaim_allocations.html"]

    @pytest.mark.django_db
    def test_reclaimallocationsview_context_contains_addresses(
        self, rf, superuser, mocker
    ):
        """Ensure addresses are added to context."""
        # Mock database call
        mocker.patch("rewards.views.is_admin_account_configured")
        mocked_addresses = mocker.patch(
            "rewards.views.reclaimable_addresses", return_value=["ADDR1", "ADDR2"]
        )

        request = rf.get(reverse("reclaim_allocations"))
        request.user = superuser

        response = ReclaimAllocationsView.as_view()(request)

        context = response.context_data

        assert context["addresses"] == ["ADDR1", "ADDR2"]
        mocked_addresses.assert_called_once_with()

    @pytest.mark.django_db
    def test_reclaimallocationsview_context_contains_use_admin_account(
        self, rf, superuser, mocker
    ):
        """Ensure addresses are added to context."""
        # Mock database call
        mocked_admin = mocker.patch("rewards.views.is_admin_account_configured")
        mocker.patch(
            "rewards.views.reclaimable_addresses", return_value=["ADDR1", "ADDR2"]
        )

        request = rf.get(reverse("reclaim_allocations"))
        request.user = superuser

        response = ReclaimAllocationsView.as_view()(request)

        context = response.context_data

        assert context["use_admin_account"] == mocked_admin.return_value
        mocked_admin.assert_called_once_with()
