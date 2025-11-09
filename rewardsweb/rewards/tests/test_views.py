"""Testing module for rewards app's views."""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from core.models import Contributor
from rewards.views import (
    ClaimView,
    AddAllocationsView,
    ReclaimAllocationsView,
)

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

    # ---------------------------------------------------------------------
    # ✅ ClaimView Tests
    # ---------------------------------------------------------------------
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

        contributor = Contributor.objects.create(name="claimview", address="SOMEADDRESS")
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

    # ---------------------------------------------------------------------
    # ✅ AddAllocationsView Tests
    # ---------------------------------------------------------------------
    @pytest.mark.django_db
    def test_addallocationsview_requires_login(self, rf):
        request = rf.get(reverse("add_allocations"))
        request.user = AnonymousUser()

        response = AddAllocationsView.as_view()(request)

        assert response.status_code == 302
        assert "/login" in response.url.lower()

    @pytest.mark.django_db
    def test_addallocationsview_superuser_can_access(self, rf, superuser):
        request = rf.get(reverse("add_allocations"))
        request.user = superuser

        response = AddAllocationsView.as_view()(request)

        assert response.status_code == 200
        assert response.template_name == ["rewards/add_allocations.html"]

    # ---------------------------------------------------------------------
    # ✅ ReclaimAllocationsView Tests
    # ---------------------------------------------------------------------
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
