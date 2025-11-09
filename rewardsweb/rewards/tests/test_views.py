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
    def test_addallocationsview_requires_login(self,rf):
        """Ensure the view redirects anonymous users to login page."""
        request = rf.get("/rewards/add-allocations/")
        request.user = AnonymousUser()

        response = AddAllocationsView.as_view()(request)

        assert response.status_code == 302  # redirect
        assert "/login" in response.url.lower()

    @pytest.mark.django_db
    def test_addallocationsview_superuser_can_access(self,rf, superuser):
        """Superusers should be able to access the page."""
        request = rf.get("/rewards/add-allocations/")
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        assert response.status_code == 200
        assert response.template_name == ["rewards/add_allocations.html"]

    @pytest.mark.django_db
    def test_addallocationsview_context_contains_addresses_and_amounts(
        self,rf, superuser, mocker
    ):
        """Ensure addresses + amounts from queryset are added to context."""

        # Mock database call
        mocked_contribs = mocker.patch(
            "rewards.views.Contribution.objects.addressed_contributions",
            return_value=(["ADDR1", "ADDR2"], [10, 20]),
        )

        request = rf.get("/rewards/add-allocations/")
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        context = response.context_data

        assert context["addresses"] == ["ADDR1", "ADDR2"]
        assert context["amounts"] == [10, 20]
        # Ensures function was called exactly once
        mocked_contribs.assert_called_once_with()

    @pytest.mark.django_db
    def test_addallocationsview_normal_user_blocked(self,rf, user):
        """Non-superusers should NOT be allowed to access the page."""
        request = rf.get("/rewards/add-allocations/")
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
    def test_reclaimallocationsview_superuser_can_access(self, rf, superuser):
        request = rf.get(reverse("reclaim_allocations"))
        request.user = superuser

        response = ReclaimAllocationsView.as_view()(request)

        assert response.status_code == 200
        assert response.template_name == ["rewards/reclaim_allocations.html"]
