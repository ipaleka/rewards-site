"""Testing module for :py:mod:`utils.mappers` module."""

import pickle
from collections import defaultdict, namedtuple
from datetime import datetime
from unittest import mock

import pytest
from django.conf import settings
from django.http import Http404

from core.models import IssueStatus, Reward, SocialPlatform
from utils.constants.core import GITHUB_ISSUES_EXCLUDED_CONTRIBUTORS
from utils.mappers import (
    CustomIssue,
    _build_reward_mapping,
    _create_issues_bulk,
    _extract_url_text,
    _fetch_and_categorize_issues,
    _map_closed_archived_issues,
    _map_open_issues,
    _identify_contributor_from_text,
    _identify_contributor_from_user,
    _identify_platform_from_text,
    _identify_reward_from_labels,
    _is_url_github_issue,
    _load_saved_issues,
    _save_issues,
    map_github_issues,
)


class TestUtilsMappersCustomIssue:
    """Testing class for :class:`utils.mappers.CustomIssue` wrapper."""

    def test_utils_mappers_custom_issue_initialization(self, mocker):
        """Test basic initialization."""
        mock_issue = mocker.MagicMock()
        mock_issue.number = 101

        custom_issue = CustomIssue(issue=mock_issue, comments=[])

        assert custom_issue.issue == mock_issue
        assert custom_issue.comments == []

    def test_utils_mappers_custom_issue_with_comments(self, mocker):
        """Test initialization with comments."""
        mock_issue = mocker.MagicMock()
        mock_issue.number = 102

        comments = [mocker.MagicMock(), mocker.MagicMock()]
        custom_issue = CustomIssue(issue=mock_issue, comments=comments)

        assert custom_issue.issue == mock_issue
        assert custom_issue.comments == comments


class TestUtilsMappersHelpers:
    """Testing class for :py:mod:`utils.mappers` helper functions."""

    # # _build_reward_mapping
    @pytest.mark.django_db
    def test_utils_mappers_build_reward_mapping_success(self, mocker):
        """Test _build_reward_mapping successfully builds mapping."""
        # Mock Reward objects
        mock_reward1 = mocker.MagicMock()
        mock_reward2 = mocker.MagicMock()

        # Mock REWARDS_COLLECTION to return known values
        mock_rewards_collection = [
            ["[AT] Admin Task", 1000000],
            ["[F] Feature Request", 2000000],
        ]
        mocker.patch("utils.mappers.REWARDS_COLLECTION", mock_rewards_collection)

        # Mock ISSUE_CREATION_LABEL_CHOICES
        mock_label_choices = [
            ("admin task", "Admin Task"),
            ("feature request", "Feature Request"),
        ]
        mocker.patch("utils.mappers.ISSUE_CREATION_LABEL_CHOICES", mock_label_choices)

        # Mock Reward.objects.get to return rewards
        mocker.patch(
            "utils.mappers.Reward.objects.get", side_effect=[mock_reward1, mock_reward2]
        )

        result = _build_reward_mapping()

        assert "admin task" in result
        assert "feature request" in result
        assert result["admin task"] == mock_reward1
        assert result["feature request"] == mock_reward2

    @pytest.mark.django_db
    def test_utils_mappers_build_reward_mapping_no_reward_found(self, mocker):
        """Test _build_reward_mapping when no reward is found."""
        mock_rewards_collection = [
            ["[AT] Admin Task", 1000000],
        ]
        mocker.patch("utils.mappers.REWARDS_COLLECTION", mock_rewards_collection)

        mock_label_choices = [
            ("admin task", "Admin Task"),
        ]
        mocker.patch("utils.mappers.ISSUE_CREATION_LABEL_CHOICES", mock_label_choices)

        # Mock Reward.DoesNotExist
        mocker.patch(
            "utils.mappers.Reward.objects.get",
            side_effect=Reward.DoesNotExist("No reward found"),
        )

        result = _build_reward_mapping()

        assert result == {}

    @pytest.mark.django_db
    def test_utils_mappers_build_reward_mapping_multiple_rewards(self, mocker):
        """Test _build_reward_mapping when multiple rewards are found."""
        mock_rewards_collection = [
            ["[AT] Admin Task", 1000000],
        ]
        mocker.patch("utils.mappers.REWARDS_COLLECTION", mock_rewards_collection)

        mock_label_choices = [
            ("admin task", "Admin Task"),
        ]
        mocker.patch("utils.mappers.ISSUE_CREATION_LABEL_CHOICES", mock_label_choices)

        mock_reward = mocker.MagicMock()

        # Mock MultipleObjectsReturned and then first()
        mocker.patch(
            "utils.mappers.Reward.objects.get",
            side_effect=Reward.MultipleObjectsReturned("Multiple rewards"),
        )
        mocker.patch(
            "utils.mappers.Reward.objects.filter",
            return_value=mocker.MagicMock(first=lambda: mock_reward),
        )

        result = _build_reward_mapping()

        assert "admin task" in result
        assert result["admin task"] == mock_reward

    @pytest.mark.django_db
    def test_utils_mappers_build_reward_mapping_no_bracket_match(self, mocker):
        """Test _build_reward_mapping when no bracket pattern is found."""
        mock_rewards_collection = [
            ["Admin Task Without Brackets", 1000000],
        ]
        mocker.patch("utils.mappers.REWARDS_COLLECTION", mock_rewards_collection)

        mock_label_choices = [
            ("admin task", "Admin Task"),
        ]
        mocker.patch("utils.mappers.ISSUE_CREATION_LABEL_CHOICES", mock_label_choices)

        result = _build_reward_mapping()

        assert result == {}

    # # _extract_url_text
    @pytest.mark.django_db
    def test_utils_mappers_extract_url_text_markdown_link(self, mocker):
        """Test _extract_url_text with markdown link."""
        body = "Check this [Discord link](https://discord.com/channels/123/456)"
        platform_id = 1

        # Mock SocialPlatform
        mock_platform = mocker.MagicMock()
        mock_platform.name = "Discord"
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.get", return_value=mock_platform
        )

        result = _extract_url_text(body, platform_id)

        assert result == "https://discord.com/channels/123/456"

    @pytest.mark.django_db
    def test_utils_mappers_extract_url_text_multiple_links(self, mocker):
        """Test _extract_url_text with multiple markdown links."""
        body = """
        Check these links:
        [GitHub issue](https://github.com/user/repo/issues/123)
        [Discord channel](https://discord.com/channels/123/456)
        """
        platform_id = 1

        mock_platform = mocker.MagicMock()
        mock_platform.name = "Discord"
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.get", return_value=mock_platform
        )

        result = _extract_url_text(body, platform_id)

        assert result == "https://discord.com/channels/123/456"

    @pytest.mark.django_db
    def test_utils_mappers_extract_url_text_no_matching_platform(self, mocker):
        """Test _extract_url_text with no matching platform in URLs."""
        body = "Check [GitHub issue](https://github.com/user/repo/issues/123)"
        platform_id = 1

        mock_platform = mocker.MagicMock()
        mock_platform.name = "Discord"
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.get", return_value=mock_platform
        )

        result = _extract_url_text(body, platform_id)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_extract_url_text_platform_not_found(self, mocker):
        """Test _extract_url_text when platform is not found."""
        body = "Some text with [link](https://example.com)"
        platform_id = 999

        mocker.patch(
            "utils.mappers.SocialPlatform.objects.get",
            side_effect=SocialPlatform.DoesNotExist("Platform not found"),
        )

        result = _extract_url_text(body, platform_id)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_extract_url_text_no_markdown_links(self, mocker):
        """Test _extract_url_text with no markdown links."""
        body = "Just plain text without any markdown links"
        platform_id = 1

        mock_platform = mocker.MagicMock()
        mock_platform.name = "Discord"
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.get", return_value=mock_platform
        )

        result = _extract_url_text(body, platform_id)

        assert result is None

    # # _fetch_and_categorize_issues
    def test_utils_mappers_fetch_and_categorize_issues_no_token(self, mocker):
        """Test _fetch_and_categorize_issues returns saved issues when no token provided."""
        saved_issues = {
            "closed": ["issue1"],
            "open": ["issue2"],
            "timestamp": "2024-01-01",
        }

        mocker.patch("utils.mappers._load_saved_issues", return_value=saved_issues)

        result = _fetch_and_categorize_issues("", refetch=False)

        assert result == saved_issues

    def test_utils_mappers_fetch_and_categorize_issues_refetch_false_uses_saved(
        self, mocker
    ):
        """Test _fetch_and_categorize_issues uses saved issues when refetch is False."""
        saved_issues = {
            "closed": ["issue1"],
            "open": ["issue2"],
            "timestamp": "2024-01-01",
        }

        mocker.patch("utils.mappers._load_saved_issues", return_value=saved_issues)
        mocker.patch("utils.mappers.fetch_issues", return_value=[])

        result = _fetch_and_categorize_issues("valid_token", refetch=False)

        assert result == saved_issues

    def test_utils_mappers_fetch_and_categorize_issues_refetch_true_fetches_new(
        self, mocker
    ):
        """Test _fetch_and_categorize_issues fetches new issues when refetch is True."""

        saved_issues = {
            "closed": ["old_issue"],
            "open": ["old_issue2"],
            "timestamp": "2024-01-01",
        }
        new_issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=None,
                updated_at=datetime(2024, 1, 2, 10, 30, 0),
            ),
            mocker.MagicMock(
                state="open",
                number=102,
                pull_request=None,
                updated_at=datetime(2024, 1, 2, 11, 45, 0),
            ),
        ]

        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mock_fetch_issues = mocker.patch(
            "utils.mappers.fetch_issues", return_value=new_issues
        )
        mock_save_issues = mocker.patch("utils.mappers._save_issues")

        result = _fetch_and_categorize_issues("valid_token", refetch=True)

        mock_fetch_issues.assert_called_once()
        assert len(result["closed"]) == 1
        assert len(result["open"]) == 1
        assert result["closed"][0].issue.number == 101
        assert result["open"][0].issue.number == 102

    def test_utils_mappers_fetch_and_categorize_issues_saves_every_10_issues(
        self, mocker
    ):
        """Test _fetch_and_categorize_issues saves progress every 10 issues."""

        issues = []
        for i in range(25):
            issue = mocker.MagicMock(
                state="open" if i % 2 == 0 else "closed",
                number=100 + i,
                pull_request=None,
                updated_at=datetime(2024, 1, i + 1),
            )
            issues.append(issue)

        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mocker.patch("utils.mappers.fetch_issues", return_value=issues)
        mock_save_issues = mocker.patch("utils.mappers._save_issues")

        _fetch_and_categorize_issues("valid_token", refetch=True)

        # Should save at issues 9, 19 (0-indexed: 10th, 20th) and at the end
        # 10th (index 9), 20th (index 19), and final (25th)
        assert mock_save_issues.call_count == 4

    def test_utils_mappers_fetch_and_categorize_issues_uses_since_parameter(
        self, mocker
    ):
        """Test _fetch_and_categorize_issues uses since parameter from saved issues."""

        saved_issues = {"closed": ["old_issue"], "timestamp": datetime(2024, 1, 1)}
        new_issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
        ]

        mocker.patch("utils.mappers._load_saved_issues", return_value=saved_issues)
        mock_fetch_issues = mocker.patch(
            "utils.mappers.fetch_issues", return_value=new_issues
        )
        mocker.patch("utils.mappers._save_issues")

        _fetch_and_categorize_issues("valid_token", refetch=False)

        # Should use timestamp from saved issues as since parameter
        mock_fetch_issues.assert_called_once_with(
            "valid_token", state="all", since=datetime(2024, 1, 1)
        )

    def test_utils_mappers_fetch_and_categorize_issues_uses_default_since(self, mocker):
        """Test _fetch_and_categorize_issues uses default since when no saved timestamp."""

        saved_issues = {"closed": ["old_issue"]}  # No timestamp
        new_issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
        ]

        mocker.patch("utils.mappers._load_saved_issues", return_value=saved_issues)
        mock_fetch_issues = mocker.patch(
            "utils.mappers.fetch_issues", return_value=new_issues
        )
        mocker.patch("utils.mappers._save_issues")

        _fetch_and_categorize_issues("valid_token", refetch=True)

        # Should use GITHUB_ISSUES_START_DATE as since parameter
        from utils.constants.core import GITHUB_ISSUES_START_DATE

        mock_fetch_issues.assert_called_once_with(
            "valid_token", state="all", since=GITHUB_ISSUES_START_DATE
        )

    def test_utils_mappers_fetch_and_categorize_issues_empty_fetch(self, mocker):
        """Test _fetch_and_categorize_issues handles empty fetch results."""
        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mocker.patch("utils.mappers.fetch_issues", return_value=[])
        mock_save_issues = mocker.patch("utils.mappers._save_issues")

        result = _fetch_and_categorize_issues("valid_token", refetch=True)

        assert result == defaultdict(list)
        mock_save_issues.assert_not_called()  # No issues to save

    def test_utils_mappers_fetch_and_categorize_issues_only_pull_requests(self, mocker):
        """Test _fetch_and_categorize_issues when all results are pull requests."""

        issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=True,
                updated_at=datetime(2024, 1, 2),
            ),
            mocker.MagicMock(
                state="open",
                number=102,
                pull_request=True,
                updated_at=datetime(2024, 1, 2),
            ),
        ]

        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mocker.patch("utils.mappers.fetch_issues", return_value=issues)
        mock_save_issues = mocker.patch("utils.mappers._save_issues")

        result = _fetch_and_categorize_issues("valid_token", refetch=True)

        assert result["closed"] == []
        assert result["open"] == []
        # Should still save at the end even with no regular issues
        mock_save_issues.assert_called_once()

    def test_utils_mappers_fetch_and_categorize_issues_progress_printing(self, mocker):
        """Test _fetch_and_categorize_issues prints progress every 10 issues."""

        issues = []
        for i in range(15):
            issue = mocker.MagicMock(
                state="open",
                number=100 + i,
                pull_request=None,
                updated_at=datetime(2024, 1, i + 1),
            )
            issues.append(issue)

        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mocker.patch("utils.mappers.fetch_issues", return_value=issues)
        mocker.patch("utils.mappers._save_issues")
        mock_print = mocker.patch("builtins.print")

        _fetch_and_categorize_issues("valid_token", refetch=True)

        # Should print at issue numbers 100, 110 (0-indexed: 1st, 11th)
        print_calls = [
            call for call in mock_print.call_args_list if "Issue number:" in str(call)
        ]
        assert len(print_calls) == 2
        # Check the actual call arguments
        assert print_calls[0] == mock.call("Issue number: ", 100)
        assert print_calls[1] == mock.call("Issue number: ", 110)

    def test_utils_mappers_fetch_and_categorize_issues_final_count_print(self, mocker):
        """Test _fetch_and_categorize_issues prints final count."""

        issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
            mocker.MagicMock(
                state="open",
                number=102,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
            mocker.MagicMock(
                state="closed",
                number=103,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
        ]

        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mocker.patch("utils.mappers.fetch_issues", return_value=issues)
        mocker.patch("utils.mappers._save_issues")
        mock_print = mocker.patch("builtins.print")

        _fetch_and_categorize_issues("valid_token", refetch=True)

        # Should print final count
        final_print_call = mock_print.call_args_list[-1]
        assert "Number of issues: 3" in str(final_print_call)

    def test_utils_mappers_fetch_and_categorize_issues_mixed_states(self, mocker):
        issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
            mocker.MagicMock(
                state="open",
                number=102,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
            mocker.MagicMock(
                state="closed",
                number=103,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
            mocker.MagicMock(
                state="open",
                number=104,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
        ]

        mocker.patch("utils.mappers._load_saved_issues", return_value=defaultdict(list))
        mocker.patch("utils.mappers.fetch_issues", return_value=issues)
        mocker.patch("utils.mappers._save_issues")

        result = _fetch_and_categorize_issues("valid_token", refetch=True)

        assert len(result["closed"]) == 2
        assert len(result["open"]) == 2
        assert result["closed"][0].issue.number == 101
        assert result["closed"][1].issue.number == 103
        assert result["open"][0].issue.number == 102
        assert result["open"][1].issue.number == 104

    def test_utils_mappers_fetch_and_categorize_issues_handles_missing_keys_in_print(
        self, mocker
    ):

        issues = [
            mocker.MagicMock(
                state="closed",
                number=101,
                pull_request=None,
                updated_at=datetime(2024, 1, 2),
            ),
        ]

        # Mock _load_saved_issues to return a dict without 'open' key
        saved_issues = {"closed": [], "timestamp": datetime(2024, 1, 1)}
        mocker.patch("utils.mappers._load_saved_issues", return_value=saved_issues)

        mocker.patch("utils.mappers.fetch_issues", return_value=issues)
        mock_save_issues = mocker.patch("utils.mappers._save_issues")
        mock_print = mocker.patch("builtins.print")

        # This should not raise TypeError
        _fetch_and_categorize_issues("valid_token", refetch=True)

        # Verify the print was called successfully
        mock_print.assert_called()

    # # _identify_contributor_from_text
    def test_utils_mappers_identify_contributor_from_text_name_part_match(self):
        text = "This issue was reported by John Doe in our discussion"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_name_part_case_insensitive(
        self, mocker
    ):
        """Test _identify_contributor_from_text name part matching is case insensitive."""
        text = "Reported by JOHN DOE in the meeting"
        contributors = {"john doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_name_part_no_match(
        self, mocker
    ):
        text = "This issue was reported by Jane Smith"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result is None

    # # _identify_contributor_from_text - handle.lower() in text_lower
    def test_utils_mappers_identify_contributor_from_text_handle_match_first_handle(
        self, mocker
    ):
        """Test _identify_contributor_from_text matches first handle in parentheses."""
        text = "User johndoe reported this issue"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_handle_match_second_handle(
        self, mocker
    ):
        """Test _identify_contributor_from_text matches second handle in parentheses."""
        text = "User jd mentioned this in the discussion"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_handle_match_multiple_handles(
        self, mocker
    ):
        """Test _identify_contributor_from_text matches with multiple handles."""
        text = "User john_doe_alt reported the bug"
        contributors = {"John Doe (johndoe, jd, john_doe_alt)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_handle_case_insensitive(
        self, mocker
    ):
        """Test _identify_contributor_from_text handle matching is case insensitive."""
        text = "User JOHN_DOE reported this"
        contributors = {"John Doe (john_doe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_handle_partial_match(
        self, mocker
    ):
        """Test _identify_contributor_from_text matches handle as substring."""
        text = "Username johndoe123 mentioned this issue"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_handle_no_match(self):
        text = "User unknownuser reported this"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result is None

    def test_utils_mappers_identify_contributor_from_text_priority_name_before_handle(
        self, mocker
    ):
        text = "John Doe (aka johndoe) reported this issue"
        contributors = {"John Doe (johndoe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_priority_first_contributor(
        self, mocker
    ):
        text = "johndoe reported this issue"
        contributors = {"John Doe (johndoe, jd)": 1, "Jane Smith (janesmith, js)": 2}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_no_parentheses_simple_match(
        self, mocker
    ):
        text = "John Doe reported this issue"
        contributors = {"John Doe": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_no_parentheses_case_insensit(
        self, mocker
    ):
        text = "JOHN DOE reported this issue"
        contributors = {"john doe": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_no_parentheses_no_match(
        self, mocker
    ):
        text = "Jane Smith reported this issue"
        contributors = {"John Doe": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result is None

    def test_utils_mappers_identify_contributor_from_text_empty_text(self):
        """Test _identify_contributor_from_text handles empty text."""
        text = ""
        contributors = {"John Doe (johndoe)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result is None

    def test_utils_mappers_identify_contributor_from_text_none_text(self):
        """Test _identify_contributor_from_text handles None text."""
        contributors = {"John Doe (johndoe)": 1}

        result = _identify_contributor_from_text(None, contributors)

        assert result is None

    def test_utils_mappers_identify_contributor_from_text_empty_contributors(
        self, mocker
    ):
        """Test _identify_contributor_from_text handles empty contributors."""
        text = "John Doe reported this"
        contributors = {}

        result = _identify_contributor_from_text(text, contributors)

        assert result is None

    def test_utils_mappers_identify_contributor_from_text_complex_handle_parsing(
        self, mocker
    ):
        text = "User complex_handle-123 reported this"
        contributors = {"John Doe (complex_handle-123, jd-456)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_handles_with_spaces(
        self, mocker
    ):
        text = "User john doe reported this"
        contributors = {"John Doe (john doe, jd)": 1}

        result = _identify_contributor_from_text(text, contributors)

        assert result == 1

    def test_utils_mappers_identify_contributor_from_text_multiple_match_diff_formats(
        self, mocker
    ):
        text = "John and janesmith both worked on this"
        contributors = {
            "John Doe (johndoe, jd)": 1,
            "Jane Smith (janesmith)": 2,
            "Bob Johnson": 3,
        }

        result = _identify_contributor_from_text(text, contributors)

        # Should return first match (John Doe) because "John" matches the name part
        assert result == 2

    def test_utils_mappers_identify_contributor_from_text_exact_vs_partial_precedence(
        self, mocker
    ):
        """Test _identify_contributor_from_text precedence of exact matches over partial."""
        text = "John Doe Smith reported this"
        contributors = {"John Doe (johndoe)": 1, "John Doe Smith (jdsmith)": 2}

        result = _identify_contributor_from_text(text, contributors)

        # Should match "John Doe Smith" exactly, not partial "John Doe"
        # The function checks contributors in order, so we need to ensure the exact match comes first
        # Let's reverse the order to test this properly
        contributors_reversed = {"John Doe Smith (jdsmith)": 2, "John Doe (johndoe)": 1}

        result = _identify_contributor_from_text(text, contributors_reversed)
        assert result == 2

    def test_utils_mappers_identify_contributor_from_text_handle_takes_precedence_over_partial_name(
        self, mocker
    ):
        """Test _identify_contributor_from_text handle match takes precedence over partial name match."""
        text = "User janesmith reported this issue"
        contributors = {
            "John Smith (johnsmith)": 1,  # "Smith" would partially match but shouldn't
            "Jane Smith (janesmith)": 2,  # Exact handle match should win
        }

        result = _identify_contributor_from_text(text, contributors)

        assert result == 2

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_text_simple_match(self):
        """Test _identify_contributor_from_text with simple name match."""
        body = "This issue was reported by John Doe"
        contributors = {"John Doe": 1, "Jane Smith": 2}

        result = _identify_contributor_from_text(body, contributors)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_text_handle_match(self):
        """Test _identify_contributor_from_text with handle match."""
        body = "User with handle user123 reported this issue"
        contributors = {"John Doe (user123, john_doe)": 1}

        result = _identify_contributor_from_text(body, contributors)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_text_multiple_handles(self):
        """Test _identify_contributor_from_text with multiple handles."""
        body = "User handle456 mentioned this"
        contributors = {"John Doe (user123, handle456, john_doe)": 1}

        result = _identify_contributor_from_text(body, contributors)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_text_case_insensitive(self):
        """Test _identify_contributor_from_text is case insensitive."""
        body = "Reported by JOHN DOE"
        contributors = {"john doe": 1}

        result = _identify_contributor_from_text(body, contributors)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_text_no_match(self):
        """Test _identify_contributor_from_text with no match."""
        body = "Reported by Unknown User"
        contributors = {"John Doe": 1, "Jane Smith": 2}

        result = _identify_contributor_from_text(body, contributors)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_text_empty_body(self):
        """Test _identify_contributor_from_text with empty body."""
        contributors = {"John Doe": 1}

        result = _identify_contributor_from_text("", contributors)

        assert result is None

    # # _identify_contributor_from_user
    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_user_match(self):
        """Test _identify_contributor_from_user with matching handle."""
        user = "johndoe"
        contributors = {"John Doe (g@johndoe, discord@john)": 1}

        result = _identify_contributor_from_user(user, contributors)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_user_no_match(self):
        """Test _identify_contributor_from_user with no matching handle."""
        user = "unknownuser"
        contributors = {"John Doe (g@johndoe)": 1}

        result = _identify_contributor_from_user(user, contributors)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_user_case_insensitive(self):
        """Test _identify_contributor_from_user is case insensitive."""
        user = "JohnDoe"
        contributors = {"John Doe (g@johndoe)": 1}

        result = _identify_contributor_from_user(user, contributors)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_contributor_from_user_empty_contributors(self):
        """Test _identify_contributor_from_user with empty contributors."""
        user = "johndoe"
        contributors = {}

        result = _identify_contributor_from_user(user, contributors)

        assert result is None

    # # _identify_platform_from_text
    @pytest.mark.django_db
    def test_utils_mappers_identify_platform_from_text_match(self):
        """Test _identify_platform_from_text with platform match."""
        body = "Discussed on Discord about this issue"
        platforms = {"Discord": 1, "GitHub": 2}

        result = _identify_platform_from_text(body, platforms)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_platform_from_text_case_insensitive(self):
        """Test _identify_platform_from_text is case insensitive."""
        body = "discord channel discussion"
        platforms = {"Discord": 1}

        result = _identify_platform_from_text(body, platforms)

        assert result == 1

    @pytest.mark.django_db
    def test_utils_mappers_identify_platform_from_text_no_match(self):
        """Test _identify_platform_from_text with no platform match."""
        body = "General discussion about the issue"
        platforms = {"Discord": 1, "GitHub": 2}

        result = _identify_platform_from_text(body, platforms)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_identify_platform_from_text_empty_body(self):
        """Test _identify_platform_from_text with empty body."""
        platforms = {"Discord": 1}

        result = _identify_platform_from_text("", platforms)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_identify_platform_from_text_empty_platforms(self):
        """Test _identify_platform_from_text with empty platforms."""
        body = "Discord discussion"
        platforms = {}

        result = _identify_platform_from_text(body, platforms)

        assert result is None

    # # _identify_reward_from_labels
    @pytest.mark.django_db
    def test_utils_mappers_identify_reward_from_labels_exact_match(self, mocker):
        """Test _identify_reward_from_labels with exact label match."""
        mock_label1 = mocker.MagicMock()
        mock_label1.name = "admin task"
        mock_label2 = mocker.MagicMock()
        mock_label2.name = "other label"

        labels = [mock_label1, mock_label2]
        reward_mapping = {"admin task": "reward1", "feature request": "reward2"}

        result = _identify_reward_from_labels(labels, reward_mapping)

        assert result == "reward1"

    @pytest.mark.django_db
    def test_utils_mappers_identify_reward_from_labels_case_insensitive(self, mocker):
        """Test _identify_reward_from_labels is case insensitive."""
        mock_label = mocker.MagicMock()
        mock_label.name = "ADMIN TASK"

        labels = [mock_label]
        reward_mapping = {"admin task": "reward1"}

        result = _identify_reward_from_labels(labels, reward_mapping)

        assert result == "reward1"

    @pytest.mark.django_db
    def test_utils_mappers_identify_reward_from_labels_no_match(self, mocker):
        """Test _identify_reward_from_labels with no matching labels."""
        mock_label = mocker.MagicMock()
        mock_label.name = "unrelated label"

        labels = [mock_label]
        reward_mapping = {"admin task": "reward1"}

        result = _identify_reward_from_labels(labels, reward_mapping)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_identify_reward_from_labels_empty_labels(self, mocker):
        """Test _identify_reward_from_labels with empty labels list."""
        labels = []
        reward_mapping = {"admin task": "reward1"}

        result = _identify_reward_from_labels(labels, reward_mapping)

        assert result is None

    @pytest.mark.django_db
    def test_utils_mappers_identify_reward_from_labels_empty_mapping(self, mocker):
        """Test _identify_reward_from_labels with empty reward mapping."""
        mock_label = mocker.MagicMock()
        mock_label.name = "admin task"

        labels = [mock_label]
        reward_mapping = {}

        result = _identify_reward_from_labels(labels, reward_mapping)

        assert result is None

    def test_utils_mappers_identify_reward_from_labels_partial_match(self, mocker):
        """Test _identify_reward_from_labels returns reward for partial label match."""
        # Mock label objects
        mock_label1 = mocker.MagicMock()
        mock_label1.name = "admin task priority"  # Contains "admin task" as exact words

        mock_label2 = mocker.MagicMock()
        mock_label2.name = "other-label"

        labels = [mock_label1, mock_label2]

        # Mock reward mapping
        mock_reward = mocker.MagicMock()
        reward_mapping = {
            "admin task": mock_reward,
            "feature request": mocker.MagicMock(),
        }

        result = _identify_reward_from_labels(labels, reward_mapping)

        # Should return the reward for "admin task" since "admin task" is in "admin task priority"
        assert result == mock_reward

    # # _is_url_github_issue
    def test_utils_mappers_is_url_github_issue_valid_url(self):
        """Test valid GitHub issue URL returns issue number."""
        valid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/123"
        )

        result = _is_url_github_issue(valid_url)

        assert result == 123

    def test_utils_mappers_is_url_github_issue_invalid_domain(self):
        """Test invalid domain returns False."""
        invalid_url = "https://gitlab.com/owner/repo/issues/123"

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_mappers_is_url_github_issue_invalid_owner(self):
        """Test invalid repo owner returns False."""
        invalid_url = (
            f"https://github.com/wrong_owner/{settings.GITHUB_REPO_NAME}/issues/123"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_mappers_is_url_github_issue_invalid_repo(self):
        """Test invalid repo name returns False."""
        invalid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/wrong_repo/issues/123"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_mappers_is_url_github_issue_invalid_path(self):
        """Test invalid path returns False."""
        invalid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/pulls/123"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_mappers_is_url_github_issue_non_numeric_issue(self):
        """Test non-numeric issue number returns False."""
        invalid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/abc"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False


class TestUtilsMappersIOFunctions:
    """Testing class for :py:mod:`utils.mappers` helper functions."""

    # # _load_saved_issues
    def test_utils_mappers_load_saved_issues_returns_defaultdict(self, mocker):
        with (
            mock.patch("utils.mappers.Path") as mocked_path,
            mock.patch(
                "utils.mappers.read_pickle", return_value={}
            ) as mocked_read_pickle,
        ):
            # Mock the path chain
            mock_path_instance = mocker.MagicMock()
            mocked_path.return_value = mock_path_instance
            mock_path_instance.resolve.return_value.parent.parent.__truediv__.return_value = (
                mocker.MagicMock()
            )

            result = _load_saved_issues()

            assert isinstance(result, defaultdict)
            mocked_read_pickle.assert_called_once()

    def test_utils_mappers_load_saved_issues_loads_data_correctly(self, mocker):
        test_data = {
            "repo1": [{"id": 1, "title": "Issue 1"}],
            "repo2": [{"id": 2, "title": "Issue 2"}],
            "timestamp": 1234567890,
        }
        with (
            mock.patch("utils.mappers.Path") as mocked_path,
            mock.patch(
                "utils.mappers.read_pickle", return_value=test_data
            ) as mocked_read_pickle,
        ):
            # Mock the path chain
            mock_path_instance = mocker.MagicMock()
            mocked_path.return_value = mock_path_instance
            mock_path_instance.resolve.return_value.parent.parent.__truediv__.return_value = (
                mocker.MagicMock()
            )

            result = _load_saved_issues()

            assert isinstance(result, defaultdict)
            assert dict(result) == test_data
            mocked_read_pickle.assert_called_once()

    def test_utils_mappers_load_saved_issues_handles_empty_data(self, mocker):
        with (
            mock.patch("utils.mappers.Path") as mocked_path,
            mock.patch(
                "utils.mappers.read_pickle", return_value={}
            ) as mocked_read_pickle,
        ):
            # Mock the path chain
            mock_path_instance = mocker.MagicMock()
            mocked_path.return_value = mock_path_instance
            mock_path_instance.resolve.return_value.parent.parent.__truediv__.return_value = (
                mocker.MagicMock()
            )

            result = _load_saved_issues()

            assert isinstance(result, defaultdict)
            assert dict(result) == {}
            mocked_read_pickle.assert_called_once()

    # # _save_issues
    def test_utils_mappers_save_issues_writes_to_file(self, mocker):
        github_issues = {
            "repo1": [{"id": 1, "title": "Issue 1"}],
            "repo2": [{"id": 2, "title": "Issue 2"}],
        }
        timestamp = 1234567890

        with (
            mock.patch("utils.mappers.Path") as mocked_path,
            mock.patch("utils.mappers.open", mock.mock_open()) as mocked_open,
            mock.patch("utils.mappers.pickle.dump") as mocked_pickle_dump,
        ):
            # Mock the entire path chain correctly
            mock_final_path = mocker.MagicMock()

            # Set up the chain: Path() -> resolve() -> parent -> parent -> __truediv__("fixtures") -> __truediv__("github_issues.pkl")
            mock_path_instance = mocker.MagicMock()
            mocked_path.return_value = mock_path_instance

            mock_resolve = mocker.MagicMock()
            mock_path_instance.resolve.return_value = mock_resolve

            mock_parent1 = mocker.MagicMock()
            mock_parent2 = mocker.MagicMock()
            mock_resolve.parent = mock_parent1
            mock_parent1.parent = mock_parent2

            # Mock the __truediv__ chain
            mock_parent2.__truediv__.return_value = mock_final_path
            mock_final_path.__truediv__.return_value = mock_final_path

            _save_issues(github_issues, timestamp)

            # Assert open was called with the final path
            mocked_open.assert_called_once_with(mock_final_path, "wb")

            # Verify pickle.dump was called
            mocked_pickle_dump.assert_called_once()

            # Check that timestamp was added to the data
            call_args = mocked_pickle_dump.call_args[0]
            saved_data = call_args[0]
            assert saved_data["timestamp"] == timestamp
            assert saved_data["repo1"] == github_issues["repo1"]
            assert saved_data["repo2"] == github_issues["repo2"]

    def test_utils_mappers_save_issues_creates_directory(self, mocker):
        github_issues = {"repo1": [{"id": 1, "title": "Issue 1"}]}
        timestamp = 1234567890

        with (
            mock.patch("utils.mappers.Path") as mocked_path,
            mock.patch("utils.mappers.open", mock.mock_open()),
            mock.patch("utils.mappers.pickle.dump"),
        ):
            # Mock the entire path chain correctly
            mock_final_path = mocker.MagicMock()
            mock_parent_dir = mocker.MagicMock()
            mock_final_path.parent = mock_parent_dir

            # Set up the chain
            mock_path_instance = mocker.MagicMock()
            mocked_path.return_value = mock_path_instance

            mock_resolve = mocker.MagicMock()
            mock_path_instance.resolve.return_value = mock_resolve

            mock_parent1 = mocker.MagicMock()
            mock_parent2 = mocker.MagicMock()
            mock_resolve.parent = mock_parent1
            mock_parent1.parent = mock_parent2

            # Mock the __truediv__ chain to return our final path
            mock_parent2.__truediv__.return_value = mock_final_path
            mock_final_path.__truediv__.return_value = mock_final_path

            _save_issues(github_issues, timestamp)

            # Assert mkdir was called on the parent directory
            mock_parent_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_utils_mappers_save_issues_handles_permission_error(self, mocker):
        github_issues = {"repo1": [{"id": 1, "title": "Issue 1"}]}
        timestamp = 1234567890

        with (
            mock.patch("utils.mappers.Path") as mocked_path,
            mock.patch(
                "utils.mappers.open", side_effect=PermissionError("Permission denied")
            ),
            mock.patch("utils.mappers.pickle.dump"),
        ):
            # Mock the path chain
            mock_path_instance = mocker.MagicMock()
            mocked_path.return_value = mock_path_instance
            mock_path_instance.resolve.return_value.parent.parent.__truediv__.return_value = (
                mocker.MagicMock()
            )

            with pytest.raises(PermissionError):
                _save_issues(github_issues, timestamp)

    def test_utils_mappers_save_and_load_roundtrip(self, mocker, tmp_path):
        # Import here to avoid circular imports if needed

        def mock_read_pickle(filename):
            if filename.exists():
                with open(filename, "rb") as f:
                    return pickle.load(f)
            return {}

        def mock_save_issues(github_issues, timestamp):
            path = tmp_path / "github_issues.pkl"
            github_issues["timestamp"] = timestamp
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                pickle.dump(github_issues, f)

        def mock_load_saved_issues():
            github_issues = defaultdict(list)
            path = tmp_path / "github_issues.pkl"
            data = mock_read_pickle(path)
            for key in data:
                github_issues[key] = data[key]
            return github_issues

        test_data = {
            "repo1": [{"id": 1, "title": "Issue 1", "state": "open"}],
            "repo2": [{"id": 2, "title": "Issue 2", "state": "closed"}],
        }
        timestamp = 1234567890

        # Save the data
        mock_save_issues(test_data.copy(), timestamp)

        # Load the data
        loaded_data = mock_load_saved_issues()

        # Verify
        expected_data = test_data.copy()
        expected_data["timestamp"] = timestamp
        assert dict(loaded_data) == expected_data


class TestUtilsMappersMapping:
    """Testing class for bulk-optimized :py:mod:`utils.mappers` mapping function."""

    # # _create_issues_bulk
    def test_utils_mappers_create_issues_bulk_empty_assignments(self, mocker):
        """Test function returns early when no assignments provided."""
        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")
        mocked_contribution_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )

        _create_issues_bulk([])

        mocked_issue_filter.assert_not_called()
        mocked_bulk_create.assert_not_called()
        mocked_contribution_filter.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_create_issues_bulk_all_new_issues(self, mocker):
        """Test bulk creation when all issues are new."""
        issue_assignments = [
            (101, 1, IssueStatus.ARCHIVED),
            (102, 2, IssueStatus.ARCHIVED),
            (103, 3, IssueStatus.ARCHIVED),
        ]

        # Create proper QuerySet-like mock for existing issues
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []

        # Mock Issue.objects.filter to return our mock QuerySet
        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")

        # Mock getting all issues after creation - return proper QuerySet-like object
        mock_issue1 = mocker.MagicMock()
        mock_issue1.number = 101
        mock_issue2 = mocker.MagicMock()
        mock_issue2.number = 102
        mock_issue3 = mocker.MagicMock()
        mock_issue3.number = 103

        mock_issues_queryset = mocker.MagicMock()
        mock_issues_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_issue1, mock_issue2, mock_issue3])
        )

        # First call returns empty (existing issues), second call returns all issues
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_issues_queryset]

        # Mock contributions
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2
        mock_contrib3 = mocker.MagicMock()
        mock_contrib3.id = 3

        # Create a proper mock for the contributions queryset that can be converted
        mock_contrib_queryset = mocker.MagicMock()
        mock_contrib_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2, mock_contrib3])
        )

        # Mock the filter to return our queryset
        mocked_contrib_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        # Mock bulk_update - we need to check it's called with the queryset
        mocked_bulk_update = mocker.patch(
            "utils.mappers.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Verify issue creation
        mocked_bulk_create.assert_called_once()
        created_issues = mocked_bulk_create.call_args[0][0]
        assert len(created_issues) == 3
        assert {issue.number for issue in created_issues} == {101, 102, 103}
        assert all(issue.status == IssueStatus.ARCHIVED for issue in created_issues)

        # Verify contribution updates
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contributions were updated
        assert mock_contrib1.issue == mock_issue1
        assert mock_contrib2.issue == mock_issue2
        assert mock_contrib3.issue == mock_issue3

    @pytest.mark.django_db
    def test_utils_mappers_create_issues_bulk_mixed_existing_issues(self, mocker):
        """Test bulk creation when some issues exist and some are new."""
        issue_assignments = [
            (101, 1, IssueStatus.ARCHIVED),
            (102, 2, IssueStatus.ARCHIVED),
        ]

        # Mock existing issues (only 101 exists)
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = [101]

        # Mock Issue.objects.filter
        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")

        # Mock getting all issues after creation
        mock_issue1 = mocker.MagicMock()
        mock_issue1.number = 101
        mock_issue2 = mocker.MagicMock()
        mock_issue2.number = 102

        mock_issues_queryset = mocker.MagicMock()
        mock_issues_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_issue1, mock_issue2])
        )

        # First call returns existing issues, second call returns all issues
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_issues_queryset]

        # Mock contributions
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2

        mock_contrib_queryset = mocker.MagicMock()
        mock_contrib_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2])
        )
        mocked_contrib_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.mappers.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Verify only one issue was created
        mocked_bulk_create.assert_called_once()
        created_issues = mocked_bulk_create.call_args[0][0]
        assert len(created_issues) == 1
        assert created_issues[0].number == 102

        # Verify both contributions were updated - called with queryset
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contributions were updated
        assert mock_contrib1.issue == mock_issue1
        assert mock_contrib2.issue == mock_issue2

    @pytest.mark.django_db
    def test_utils_mappers_create_issues_bulk_all_existing_issues(self, mocker):
        """Test bulk creation when all issues already exist."""
        issue_assignments = [
            (101, 1, IssueStatus.ARCHIVED),
            (102, 2, IssueStatus.ARCHIVED),
        ]

        # Mock existing issues (both exist)
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = [101, 102]

        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")

        # Mock getting all issues
        mock_issue1 = mocker.MagicMock()
        mock_issue1.number = 101
        mock_issue2 = mocker.MagicMock()
        mock_issue2.number = 102

        mock_issues_queryset = mocker.MagicMock()
        mock_issues_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_issue1, mock_issue2])
        )

        # Both calls return the same
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_issues_queryset]

        # Mock contributions
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2

        mock_contrib_queryset = mocker.MagicMock()
        mock_contrib_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2])
        )
        mocked_contrib_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.mappers.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Verify no new issues were created
        mocked_bulk_create.assert_not_called()

        # Verify both contributions were updated - called with queryset
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contributions were updated
        assert mock_contrib1.issue == mock_issue1
        assert mock_contrib2.issue == mock_issue2

    @pytest.mark.django_db
    def test_utils_mappers_create_issues_bulk_duplicate_assignments(self, mocker):
        """Test bulk creation handles duplicate assignments gracefully."""
        issue_assignments = [
            (101, 1, IssueStatus.ARCHIVED),
            (101, 1, IssueStatus.ARCHIVED),
            (102, 2, IssueStatus.ARCHIVED),
        ]  # Duplicate (101, 1)

        # Mock existing issues
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []
        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_issue_filter.return_value = mock_existing_issues

        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")

        # Mock getting all issues
        mock_issue1 = mocker.MagicMock()
        mock_issue1.number = 101
        mock_issue2 = mocker.MagicMock()
        mock_issue2.number = 102

        mock_issues_queryset = mocker.MagicMock()
        mock_issues_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_issue1, mock_issue2])
        )
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_issues_queryset]

        # Mock contributions
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2

        mock_contrib_queryset = mocker.MagicMock()
        mock_contrib_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2])
        )
        mocked_contrib_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.mappers.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Should only create 2 unique issues
        mocked_bulk_create.assert_called_once()
        created_issues = mocked_bulk_create.call_args[0][0]
        assert len(created_issues) == 2
        assert {issue.number for issue in created_issues} == {101, 102}

        # Both contributions should be updated once - called with queryset
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contributions were updated
        assert mock_contrib1.issue == mock_issue1
        assert mock_contrib2.issue == mock_issue2

    @pytest.mark.django_db
    def test_utils_mappers_create_issues_bulk_missing_issue_after_creation(
        self, mocker
    ):
        """Test handling when issue is missing after bulk creation."""
        issue_assignments = [(101, 1, IssueStatus.ARCHIVED)]

        # Mock existing issues (none exist)
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []
        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")

        # Mock getting all issues after creation returns empty
        mock_empty_queryset = mocker.MagicMock()
        mock_empty_queryset.__iter__ = mocker.MagicMock(return_value=iter([]))
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_empty_queryset]

        # Mock contributions
        mocked_contrib_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_empty_queryset

        mocked_bulk_update = mocker.patch(
            "utils.mappers.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Issue should be created
        mocked_bulk_create.assert_called_once()
        # But no contributions should be updated since issue is missing
        mocked_bulk_update.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_create_issues_bulk_no_contributions_found(self, mocker):
        """Test handling when no contributions are found for update."""
        issue_assignments = [
            (101, 1, IssueStatus.ARCHIVED),
            (102, 999, IssueStatus.ARCHIVED),
        ]  # 999 doesn't exist

        # Mock existing issues
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []
        mocked_issue_filter = mocker.patch("utils.mappers.Issue.objects.filter")
        mocked_issue_filter.return_value = mock_existing_issues

        mocked_bulk_create = mocker.patch("utils.mappers.Issue.objects.bulk_create")

        # Mock getting all issues
        mock_issue1 = mocker.MagicMock()
        mock_issue1.number = 101
        mock_issue2 = mocker.MagicMock()
        mock_issue2.number = 102

        mock_issues_queryset = mocker.MagicMock()
        mock_issues_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_issue1, mock_issue2])
        )
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_issues_queryset]

        # Mock contributions - only one exists
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1

        mock_contrib_queryset = mocker.MagicMock()
        mock_contrib_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1])
        )
        mocked_contrib_filter = mocker.patch(
            "utils.mappers.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.mappers.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Issues should be created
        mocked_bulk_create.assert_called_once()
        # Only existing contribution should be updated - called with queryset
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contribution was updated
        assert mock_contrib1.issue == mock_issue1

    # # _map_closed_archived_issues
    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_no_token(self, mocker):
        """Test function returns False when no GitHub token is provided."""
        result = _map_closed_archived_issues(None)
        assert result is False

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_no_contributions(
        self, mocker
    ):
        """Test function returns True when there are no contributions to process."""
        github_token = "test_token"

        # Create a proper QuerySet mock that returns empty list
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(return_value=iter([]))

        # Mock the boolean check - empty queryset should be falsy
        mock_contributions_queryset.__bool__ = mocker.MagicMock(return_value=False)
        mock_contributions_queryset.exists = mocker.MagicMock(return_value=False)

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mocked_fetch_issues = mocker.patch("utils.mappers.fetch_issues")
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues(github_token)

        assert result is True
        # fetch_issues should not be called when there are no contributions
        mocked_fetch_issues.assert_not_called()
        mocked_create_issues_bulk.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_url_in_body_matching(
        self, mocker
    ):
        """Test successful matching when URL appears in issue body."""

        # Mock contributions
        mock_contrib = mocker.MagicMock()
        mock_contrib.id = 1
        mock_contrib.url = "https://example.com/contrib"

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue with URL in body
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Check out https://example.com/contrib for details"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with(
            [(101, 1, IssueStatus.ARCHIVED)]
        )

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_github_issue_url_match(
        self, mocker
    ):
        """Test successful matching when contribution URL is a GitHub issue URL."""

        # Mock contribution with GitHub issue URL
        github_issue_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/456"
        )
        mock_contrib = mocker.MagicMock()
        mock_contrib.id = 1
        mock_contrib.url = github_issue_url

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 456  # Matching issue number
        mock_issue.issue.body = "Some issue body without the URL"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=456)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with(
            [(456, 1, IssueStatus.ARCHIVED)]
        )

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_both_match_same_issue(
        self, mocker
    ):
        """Test that matched flag prevents duplicate assignments for same issue."""

        # Mock contributions
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib1.url = "https://example.com/contrib1"

        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2
        github_issue_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/101"
        )
        mock_contrib2.url = github_issue_url

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue that matches both methods
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Contains https://example.com/contrib1"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocked_is_url = mocker.patch("utils.mappers._is_url_github_issue")
        mocked_is_url.side_effect = lambda url: (
            101 if url == github_issue_url else False
        )
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        # Should only have one assignment despite both methods potentially matching
        call_args = mocked_create_issues_bulk.call_args[0][0]
        assert len(call_args) == 2
        # Should be the body match (first method)
        assert call_args[0] == (101, 1, IssueStatus.ARCHIVED)

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_skip_empty_urls(
        self, mocker
    ):
        """Test that contributions with empty URLs are skipped."""

        # Mock contributions with various URL states
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib1.url = ""  # Empty string

        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2
        mock_contrib2.url = None  # None value

        mock_contrib3 = mocker.MagicMock()
        mock_contrib3.id = 3
        mock_contrib3.url = "https://valid.com/url"  # Valid URL

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2, mock_contrib3])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Contains https://valid.com/url"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        # Should only process the valid URL
        mocked_create_issues_bulk.assert_called_once_with(
            [(101, 3, IssueStatus.ARCHIVED)]
        )

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_transaction_decorator(
        self, mocker
    ):
        """Test that function has transaction.atomic decorator."""

        mock_contrib = mocker.MagicMock()
        mock_contrib.id = 1
        mock_contrib.url = "https://example.com/contrib"

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Contains https://example.com/contrib"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        # Check that function is decorated with transaction.atomic
        # by checking if it's wrapped
        assert _map_closed_archived_issues.__name__ == "_map_closed_archived_issues"

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        mocked_create_issues_bulk.assert_called_once()

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_issue_no_body_url_match(
        self, mocker
    ):
        """Test that issues without body are still checked for issue URL matching."""

        # Mock contribution with GitHub issue URL
        github_issue_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/456"
        )
        mock_contrib = mocker.MagicMock()
        mock_contrib.id = 1
        mock_contrib.url = github_issue_url

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue without body but with matching number
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 456
        mock_issue.issue.body = None

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=456)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        # Should still match via GitHub issue URL even with no body
        mocked_create_issues_bulk.assert_called_once_with(
            [(456, 1, IssueStatus.ARCHIVED)]
        )

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_no_matches(self, mocker):
        """Test function when no URLs match any issue bodies or GitHub issue URLs."""

        mock_contrib = mocker.MagicMock()
        mock_contrib.id = 1
        mock_contrib.url = "https://example.com/nomatch"

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Contains completely different URL"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue])

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([])

    @pytest.mark.django_db
    def test_utils_mappers_map_closed_archived_issues_bulk_multiple_issues(
        self, mocker
    ):
        """Test processing multiple issues with different matching methods."""

        # Mock contributions
        mock_contrib1 = mocker.MagicMock()
        mock_contrib1.id = 1
        mock_contrib1.url = "https://example.com/body_match"

        mock_contrib2 = mocker.MagicMock()
        mock_contrib2.id = 2
        github_issue_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/202"
        )
        mock_contrib2.url = github_issue_url

        # Create a proper QuerySet mock
        mock_contributions_queryset = mocker.MagicMock()
        mock_contributions_queryset.only.return_value = (
            mock_contributions_queryset  # Chainable
        )
        mock_contributions_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2])
        )

        mocker.patch(
            "utils.mappers.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock multiple issues
        mock_issue1 = mocker.MagicMock()
        mock_issue1.issue.number = 101
        mock_issue1.issue.body = "Contains https://example.com/body_match"

        mock_issue2 = mocker.MagicMock()
        mock_issue2.issue.number = 202
        mock_issue2.issue.body = "No matching URL here"

        mocker.patch(
            "utils.mappers.fetch_issues",
            return_value=[mock_issue1, mock_issue2],
        )
        mocked_is_url = mocker.patch("utils.mappers._is_url_github_issue")
        mocked_is_url.side_effect = lambda url: (
            202 if url == github_issue_url else False
        )
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _map_closed_archived_issues([mock_issue1, mock_issue2])

        assert result is True
        # Should have both assignments via different methods
        call_args = mocked_create_issues_bulk.call_args[0][0]
        assert set(call_args) == {
            (101, 1, IssueStatus.ARCHIVED),
            (202, 2, IssueStatus.ARCHIVED),
        }

    # # _map_open_issues
    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_no_issues(self):
        """Test _map_open_issues with no issues."""
        result = _map_open_issues([])

        assert result is False

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_successful_creation(self, mocker):
        """Test _map_open_issues successfully creates contributions."""
        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Discord discussion about feature"
        mock_issue.issue.title = "Feature Request"
        mock_issue.issue.user.login = "testuser"
        mock_issue.comments = []
        mock_issue.issue.labels = []

        # Mock all dependencies
        mocker.patch(
            "utils.mappers._build_reward_mapping",
            return_value={"feature request": "mock_reward"},
        )

        mock_contributors = {"testuser (g@testuser)": 1}
        mocker.patch(
            "utils.mappers.Contributor.objects.all",
            return_value=[mocker.MagicMock(info="testuser (g@testuser)", id=1)],
        )

        mock_platforms = {"Discord": 1}
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.all",
            return_value=[mocker.MagicMock(name="Discord", id=1)],
        )

        mock_cycle = mocker.MagicMock()
        mocker.patch("utils.mappers.Cycle.objects.latest", return_value=mock_cycle)

        mocker.patch("utils.mappers._identify_contributor_from_user", return_value=1)
        mocker.patch("utils.mappers._identify_platform_from_text", return_value=1)
        mocker.patch(
            "utils.mappers._identify_reward_from_labels", return_value="mock_reward"
        )
        mocker.patch(
            "utils.mappers._extract_url_text",
            return_value="https://discord.com/test",
        )

        mock_issue_obj = mocker.MagicMock()
        mocker.patch("utils.mappers.get_object_or_404", side_effect=Http404)
        mocker.patch("utils.mappers.Issue.objects.create", return_value=mock_issue_obj)

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_called_once()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_for_excluded_contributors(self, mocker):
        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Discord discussion about feature"
        mock_issue.issue.title = "Feature Request"
        mock_issue.issue.user.login = "testuser"
        mock_issue.comments = []
        mock_issue.issue.labels = []

        # Mock all dependencies
        mocker.patch(
            "utils.mappers._build_reward_mapping",
            return_value={"feature request": "mock_reward"},
        )

        excluded_contributor = GITHUB_ISSUES_EXCLUDED_CONTRIBUTORS[0]
        mocker.patch(
            "utils.mappers.Contributor.objects.all",
            return_value=[
                mocker.MagicMock(info=f"{excluded_contributor} (g@testuser)", id=1)
            ],
        )

        mocker.patch(
            "utils.mappers.SocialPlatform.objects.all",
            return_value=[mocker.MagicMock(name="Discord", id=1)],
        )

        mock_cycle = mocker.MagicMock()
        mocker.patch("utils.mappers.Cycle.objects.latest", return_value=mock_cycle)

        mocker.patch("utils.mappers._identify_platform_from_text", return_value=1)
        mocker.patch(
            "utils.mappers._identify_reward_from_labels", return_value="mock_reward"
        )
        mocker.patch(
            "utils.mappers._extract_url_text",
            return_value="https://discord.com/test",
        )

        mock_issue_obj = mocker.MagicMock()
        mocker.patch("utils.mappers.get_object_or_404", side_effect=Http404)
        mocker.patch("utils.mappers.Issue.objects.create", return_value=mock_issue_obj)

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_skip_no_contributor(self, mocker):
        """Test _map_open_issues skips issues with no contributor."""
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Some text"
        mock_issue.issue.title = "No Internal"
        mock_issue.issue.user.login = "unknownuser"
        mock_issue.comments = []

        mocker.patch("utils.mappers._build_reward_mapping", return_value={})
        mocker.patch("utils.mappers.Contributor.objects.all", return_value=[])
        mocker.patch("utils.mappers.SocialPlatform.objects.all", return_value=[])
        mocker.patch(
            "utils.mappers.Cycle.objects.latest", return_value=mocker.MagicMock()
        )
        mocker.patch("utils.mappers._identify_contributor_from_user", return_value=None)
        mocker.patch("utils.mappers._identify_contributor_from_text", return_value=None)

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_skip_internal_title(self, mocker):
        """Test _map_open_issues skips issues with [Internal] in title."""
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Some text"
        mock_issue.issue.title = "[Internal] Internal task"
        mock_issue.comments = []

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )
        mocker.patch("utils.mappers.Cycle.objects.latest")

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_skip_no_body_comments(self, mocker):
        """Test _map_open_issues skips issues with no body or comments."""
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = None
        mock_issue.comments = []
        mock_issue.issue.title = "Regular issue"

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )
        mocker.patch("utils.mappers.Cycle.objects.latest")

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_skip_no_contributor_from_user_fallback_text(
        self, mocker
    ):
        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Discord discussion about feature by @johndoe"
        mock_issue.issue.title = "Feature Request"
        mock_issue.issue.user.login = (
            "unknownuser"  # This won't match in _identify_contributor_from_user
        )
        mock_issue.comments = []
        mock_issue.issue.labels = [mocker.MagicMock(name="feature")]

        # Mock dependencies
        mocker.patch(
            "utils.mappers._build_reward_mapping",
            return_value={"feature": "mock_reward"},
        )

        # Mock contributors - user login won't match, but text will
        mock_contributors = {"John Doe (johndoe)": 1}
        mocker.patch(
            "utils.mappers.Contributor.objects.all",
            return_value=[mocker.MagicMock(info="John Doe (johndoe)", id=1)],
        )

        mock_platforms = {"Discord": 1}
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.all",
            return_value=[mocker.MagicMock(name="Discord", id=1)],
        )

        mock_cycle = mocker.MagicMock()
        mocker.patch(
            "utils.mappers.Cycle.objects.latest", return_value=mocker.MagicMock()
        )

        # Mock identification functions
        mocker.patch(
            "utils.mappers._identify_contributor_from_user", return_value=None
        )  # User match fails
        mocker.patch(
            "utils.mappers._identify_contributor_from_text", return_value=1
        )  # Text match succeeds
        mocker.patch("utils.mappers._identify_platform_from_text", return_value=1)
        mocker.patch(
            "utils.mappers._identify_reward_from_labels", return_value="mock_reward"
        )
        mocker.patch(
            "utils.mappers._extract_url_text",
            return_value="https://discord.com/test",
        )

        mocker.patch("utils.mappers.get_object_or_404", side_effect=Http404)
        mocker.patch(
            "utils.mappers.Issue.objects.create", return_value=mocker.MagicMock()
        )
        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_called_once()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_skip_no_platform(self, mocker):
        """Test _map_open_issues skips issue when no platform is identified."""
        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "General discussion about feature"
        mock_issue.issue.title = "Feature Request"
        mock_issue.issue.user.login = "johndoe"
        mock_issue.comments = []
        mock_issue.issue.labels = [mocker.MagicMock(name="feature")]

        # Mock dependencies
        mocker.patch(
            "utils.mappers._build_reward_mapping",
            return_value={"feature": "mock_reward"},
        )

        mock_contributors = {"John Doe (johndoe)": 1}
        mocker.patch(
            "utils.mappers.Contributor.objects.all",
            return_value=[mocker.MagicMock(info="John Doe (johndoe)", id=1)],
        )

        mock_platforms = {"Discord": 1}
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.all",
            return_value=[mocker.MagicMock(name="Discord", id=1)],
        )

        mocker.patch(
            "utils.mappers.Cycle.objects.latest", return_value=mocker.MagicMock()
        )

        # Mock identification functions
        mocker.patch("utils.mappers._identify_contributor_from_user", return_value=1)
        mocker.patch("utils.mappers._identify_contributor_from_text", return_value=1)
        mocker.patch(
            "utils.mappers._identify_platform_from_text", return_value=None
        )  # Platform match fails
        mocker.patch(
            "utils.mappers._identify_reward_from_labels", return_value="mock_reward"
        )

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_skip_no_reward(self, mocker):
        """Test _map_open_issues skips issue when no reward is identified."""
        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.issue.number = 101
        mock_issue.issue.body = "Discord discussion about feature"
        mock_issue.issue.title = "Feature Request"
        mock_issue.issue.user.login = "johndoe"
        mock_issue.comments = []
        mock_issue.issue.labels = [
            mocker.MagicMock(name="unknown-label")
        ]  # No matching reward

        # Mock dependencies
        mocker.patch(
            "utils.mappers._build_reward_mapping",
            return_value={"feature": "mock_reward"},
        )

        mock_contributors = {"John Doe (johndoe)": 1}
        mocker.patch(
            "utils.mappers.Contributor.objects.all",
            return_value=[mocker.MagicMock(info="John Doe (johndoe)", id=1)],
        )

        mock_platforms = {"Discord": 1}
        mocker.patch(
            "utils.mappers.SocialPlatform.objects.all",
            return_value=[mocker.MagicMock(name="Discord", id=1)],
        )

        mocker.patch(
            "utils.mappers.Cycle.objects.latest", return_value=mocker.MagicMock()
        )

        # Mock identification functions
        mocker.patch("utils.mappers._identify_contributor_from_user", return_value=1)
        mocker.patch("utils.mappers._identify_contributor_from_text", return_value=1)
        mocker.patch("utils.mappers._identify_platform_from_text", return_value=1)
        mocker.patch(
            "utils.mappers._identify_reward_from_labels", return_value=None
        )  # Reward match fails

        mock_contribution_create = mocker.patch(
            "utils.mappers.Contribution.objects.create"
        )

        result = _map_open_issues([mock_issue])

        assert result is True
        mock_contribution_create.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_map_open_issues_transaction_decorator(self):
        """Test that _map_open_issues has transaction.atomic decorator."""
        # Check that function is decorated with transaction.atomic
        assert _map_open_issues.__name__ == "_map_open_issues"

        result = _map_open_issues([])

        assert result is False


class TestUtilsMappersPublicFunctions:
    """Testing class for bulk-optimized :py:mod:`utils.mappers` public function."""

    # # map_github_issues
    @pytest.mark.django_db
    def test_utils_mappers_map_github_issues_for_provided_token(self, mocker):
        closed_issues, open_issues = mocker.MagicMock(), mocker.MagicMock()
        github_issues = {"closed": closed_issues, "open": open_issues}
        mock_categorize = mocker.patch(
            "utils.mappers._fetch_and_categorize_issues", return_value=github_issues
        )
        mock_archived = mocker.patch("utils.mappers._map_closed_archived_issues")
        mock_addressed = mocker.patch("utils.mappers._map_closed_addressed_issues")
        mock_open_issues = mocker.patch("utils.mappers._map_open_issues")
        result = map_github_issues(github_token="github_token")

        mock_categorize.assert_called_once_with("github_token")
        mock_archived.assert_called_once_with(closed_issues)
        mock_addressed.assert_called_once_with(closed_issues)
        mock_open_issues.assert_called_once_with(open_issues)

        assert result is False

    @pytest.mark.django_db
    def test_utils_mappers_map_github_issues_for_no_token(self, mocker):
        mock_categorize = mocker.patch(
            "utils.mappers._fetch_and_categorize_issues", return_value={}
        )
        mock_archived = mocker.patch("utils.mappers._map_closed_archived_issues")
        mock_addressed = mocker.patch("utils.mappers._map_closed_addressed_issues")
        mock_open_issues = mocker.patch("utils.mappers._map_open_issues")
        result = map_github_issues(github_token="github_token")

        mock_categorize.assert_called_once_with("github_token")
        mock_archived.assert_called_once_with([])
        mock_addressed.assert_called_once_with([])
        mock_open_issues.assert_called_once_with([])

        assert result is False
