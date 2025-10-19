"""Unit tests for :py:mod:`rewardsbot.models.contribution` module.

This module contains tests for the Contribution class and its
formatting functionality.
"""

from rewardsbot.models.contribution import Contribution, _create_link


class TestModelsContribution:
    """Testing class for :py:mod:`rewardsbot.models.contribution` components."""

    # # _create_link function
    def test_models_contribution_create_link_with_url(self):
        """Test _create_link function with URL creates markdown link."""
        result = _create_link("Test Link", "https://example.com")
        assert result == "[Test Link](https://example.com)"

    def test_models_contribution_create_link_without_url(self):
        """Test _create_link function without URL returns plain text."""
        result = _create_link("Test Link", None)
        assert result == "Test Link"

    def test_models_contribution_create_link_empty_url(self):
        """Test _create_link function with empty URL returns plain text."""
        result = _create_link("Test Link", "")
        assert result == "Test Link"

    # # Contribution initialization
    def test_models_contribution_initialization_with_full_data(self):
        """Test Contribution initialization with complete data."""
        data = {
            "id": 123,
            "contributor_name": "test_user",
            "cycle_id": 5,
            "platform": "discord",
            "url": "https://example.com/contribution",
            "type": "[F] Forum Post",
            "level": 2,
            "percentage": 75,
            "reward": 1500,
            "confirmed": True,
        }
        contribution = Contribution(data)

        assert contribution.id == 123
        assert contribution.contributor_name == "test_user"
        assert contribution.cycle_id == 5
        assert contribution.platform == "discord"
        assert contribution.url == "https://example.com/contribution"
        assert contribution.type == "[F] Forum Post"
        assert contribution.level == 2
        assert contribution.percentage == 75
        assert contribution.reward == 1500
        assert contribution.confirmed is True

    def test_models_contribution_initialization_with_partial_data(self):
        """Test Contribution initialization with missing optional fields."""
        data = {
            "contributor_name": "partial_user",
            "type": "[B] Blog Post",
            "level": 1,
        }
        contribution = Contribution(data)

        assert contribution.id is None
        assert contribution.contributor_name == "partial_user"
        assert contribution.cycle_id is None
        assert contribution.platform is None
        assert contribution.url is None
        assert contribution.type == "[B] Blog Post"
        assert contribution.level == 1
        assert contribution.percentage is None
        assert contribution.reward is None
        assert contribution.confirmed is None

    def test_models_contribution_initialization_with_empty_data(self):
        """Test Contribution initialization with empty data dictionary."""
        data = {}
        contribution = Contribution(data)

        assert contribution.id is None
        assert contribution.contributor_name is None
        assert contribution.cycle_id is None
        assert contribution.platform is None
        assert contribution.url is None
        assert contribution.type is None
        assert contribution.level is None
        assert contribution.percentage is None
        assert contribution.reward is None
        assert contribution.confirmed is None

    # # Contribution.formatted_contributions - user summary format
    def test_models_contribution_formatted_contributions_user_summary_confirmed(self):
        """Test formatted_contributions for user summary with confirmed contribution."""
        data = {
            "contributor_name": "test_user",
            "type": "[F] Forum Post",
            "level": 2,
            "url": "https://example.com/post",
            "reward": 2000,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[F2](https://example.com/post) 2,000 ✅"

    def test_models_contribution_formatted_contributions_user_summary_unconfirmed(self):
        """Test formatted_contributions for user summary with unconfirmed contribution."""
        data = {
            "contributor_name": "test_user",
            "type": "[B] Blog Post",
            "level": 1,
            "url": "https://example.com/blog",
            "reward": 1000,
            "confirmed": False,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[B1](https://example.com/blog) 1,000 ⍻"

    def test_models_contribution_formatted_contributions_user_summary_no_reward(self):
        """Test formatted_contributions for user summary with no reward."""
        data = {
            "contributor_name": "test_user",
            "type": "[AT] Article Translation",
            "level": 3,
            "url": "https://example.com/translation",
            "reward": None,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[AT3](https://example.com/translation) 0 ✅"

    def test_models_contribution_formatted_contributions_user_summary_zero_reward(self):
        """Test formatted_contributions for user summary with zero reward."""
        data = {
            "contributor_name": "test_user",
            "type": "[CT] Code Translation",
            "level": 2,
            "url": "https://example.com/code",
            "reward": 0,
            "confirmed": False,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[CT2](https://example.com/code) 0 ⍻"

    def test_models_contribution_formatted_contributions_user_summary_no_url(self):
        """Test formatted_contributions for user summary without URL."""
        data = {
            "contributor_name": "test_user",
            "type": "[IC] Community Interaction",
            "level": 1,
            "url": None,
            "reward": 500,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "IC1 500 ✅"

    # # Contribution.formatted_contributions - full format
    def test_models_contribution_formatted_contributions_full_format_confirmed(self):
        """Test formatted_contributions for full format with confirmed contribution."""
        data = {
            "contributor_name": "test_contributor",
            "type": "[F] Forum Post",
            "level": 3,
            "url": "https://example.com/forum",
            "reward": 3000,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        assert result == "[test_contributor [F3]](https://example.com/forum) 3,000 ✅"

    def test_models_contribution_formatted_contributions_full_format_unconfirmed(self):
        """Test formatted_contributions for full format with unconfirmed contribution."""
        data = {
            "contributor_name": "another_user",
            "type": "[B] Blog Post",
            "level": 2,
            "url": "https://example.com/article",
            "reward": 1500,
            "confirmed": False,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        assert result == "[another_user [B2]](https://example.com/article) 1,500 ⍻"

    def test_models_contribution_formatted_contributions_full_format_no_url(self):
        """Test formatted_contributions for full format without URL."""
        data = {
            "contributor_name": "no_url_user",
            "type": "[TWR] Twitter Thread",
            "level": 1,
            "url": None,
            "reward": 800,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        assert result == "no_url_user [TWR1] 800 ✅"

    # # Contribution.formatted_contributions - type parsing
    def test_models_contribution_formatted_contributions_type_with_brackets(self):
        """Test formatted_contributions with type containing brackets."""
        data = {
            "contributor_name": "bracket_user",
            "type": "[F] Detailed Forum Analysis",
            "level": 2,
            "url": "https://example.com/analysis",
            "reward": 2500,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[F2](https://example.com/analysis) 2,500 ✅"

    def test_models_contribution_formatted_contributions_type_without_brackets(self):
        """Test formatted_contributions with type without brackets."""
        data = {
            "contributor_name": "no_bracket_user",
            "type": "Forum Post",
            "level": 1,
            "url": "https://example.com/post",
            "reward": 1000,
            "confirmed": False,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[Forum Post1](https://example.com/post) 1,000 ⍻"

    def test_models_contribution_formatted_contributions_type_empty_string(self):
        """Test formatted_contributions with empty type string."""
        data = {
            "contributor_name": "empty_type_user",
            "type": "",
            "level": 1,
            "url": "https://example.com/empty",
            "reward": 500,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        assert result == "[1](https://example.com/empty) 500 ✅"

    def test_models_contribution_formatted_contributions_type_none(self):
        """Test formatted_contributions with None type."""
        data = {
            "contributor_name": "none_type_user",
            "type": None,
            "level": 2,
            "url": "https://example.com/none",
            "reward": 1200,
            "confirmed": False,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=True)

        # With None type, it should use empty string for type_short
        assert result == "[2](https://example.com/none) 1,200 ⍻"

    # # Contribution.formatted_contributions - edge cases
    def test_models_contribution_formatted_contributions_large_reward_number(self):
        """Test formatted_contributions with large reward number formatting."""
        data = {
            "contributor_name": "large_reward_user",
            "type": "[F] Major Contribution",
            "level": 3,
            "url": "https://example.com/major",
            "reward": 1234567,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        assert (
            result == "[large_reward_user [F3]](https://example.com/major) 1,234,567 ✅"
        )

    def test_models_contribution_formatted_contributions_no_contributor_name(self):
        """Test formatted_contributions without contributor name in full format."""
        data = {
            "contributor_name": None,
            "type": "[F] Forum Post",
            "level": 1,
            "url": "https://example.com/anonymous",
            "reward": 600,
            "confirmed": True,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        # With None contributor_name, it should use empty string
        assert result == "[ [F1]](https://example.com/anonymous) 600 ✅"

    def test_models_contribution_formatted_contributions_empty_contributor_name(self):
        """Test formatted_contributions with empty contributor name."""
        data = {
            "contributor_name": "",
            "type": "[B] Blog Post",
            "level": 2,
            "url": "https://example.com/empty",
            "reward": 900,
            "confirmed": False,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        # With empty contributor_name, it should create proper formatting
        assert result == "[ [B2]](https://example.com/empty) 900 ⍻"

    def test_models_contribution_formatted_contributions_all_none_values(self):
        """Test formatted_contributions with all None values."""
        data = {
            "contributor_name": None,
            "type": None,
            "level": None,
            "url": None,
            "reward": None,
            "confirmed": None,
        }
        contribution = Contribution(data)
        result = contribution.formatted_contributions(is_user_summary=False)

        # Should handle all None values gracefully
        assert result == " [None] 0 ⍻"
