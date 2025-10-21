"""Module with database fixtures for core package unit tests."""

from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import (
    Contribution,
    Contributor,
    Cycle,
    SocialPlatform,
    Reward,
    RewardType,
    Issue,
)


@pytest.fixture
def superuser():
    """Create a superuser for testing."""
    return User.objects.create_superuser(
        username="superuser", email="superuser@example.com", password="testpass123"
    )


@pytest.fixture
def regular_user():
    """Create a regular user for testing."""
    return User.objects.create_user(
        username="regularuser", email="user@example.com", password="testpass123"
    )


@pytest.fixture
def cycle():
    """Create a cycle for testing."""
    return Cycle.objects.create(start="2023-01-01", end="2023-01-31")


@pytest.fixture
def contributor():
    """Create a contributor for testing."""
    return Contributor.objects.create(name="test_contributor", address="test_address")


@pytest.fixture
def social_platform():
    """Create a social platform for testing."""
    return SocialPlatform.objects.create(name="GitHub", prefix="g@")


@pytest.fixture
def reward_type():
    """Create a reward type for testing."""
    return RewardType.objects.create(label="F", name="Feature")


@pytest.fixture
def reward(reward_type):
    """Create a reward for testing."""
    return Reward.objects.create(type=reward_type, level=1, amount=1000000, active=True)


@pytest.fixture
def contribution(cycle, contributor, social_platform, reward):
    """Create a contribution for testing."""
    return Contribution.objects.create(
        contributor=contributor,
        cycle=cycle,
        platform=social_platform,
        reward=reward,
        percentage=100.0,
        url="https://example.com/contribution",
        confirmed=False,
    )


@pytest.fixture
def issue():
    """Create an issue for testing."""
    return Issue.objects.create(number=123)


@pytest.fixture
def invalidate_url(contribution):
    """URL for invalidate view."""
    return reverse(
        "contribution-invalidate",
        kwargs={"pk": contribution.pk, "reaction": "duplicate"},
    )


@pytest.fixture
def mock_message_from_url():
    """Mock the message_from_url function."""
    with mock.patch("core.views.message_from_url") as mock_message:
        mock_message.return_value = {
            "success": True,
            "author": "test_user",
            "timestamp": "2024-01-01T12:00:00.000000+00:00",
            "content": "Test message content",
        }
        yield mock_message
