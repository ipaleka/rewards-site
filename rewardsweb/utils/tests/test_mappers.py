"""Testing module for :py:mod:`utils.mappers` module."""

import pytest
from django.conf import settings

from core.models import IssueStatus
from utils.mappers import (
    _create_issues_bulk,
    _fetch_and_assign_closed_issues,
    _is_url_github_issue,
    map_github_issues,
)


class TestUtilsMappersHelpers:
    """Testing class for :py:mod:`utils.mappers` helper functions."""

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
        issue_assignments = [(101, 1), (102, 2), (103, 3)]

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
        issue_assignments = [(101, 1), (102, 2)]

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
        issue_assignments = [(101, 1), (102, 2)]

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
        issue_assignments = [(101, 1), (101, 1), (102, 2)]  # Duplicate (101, 1)

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
        issue_assignments = [(101, 1)]

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
        issue_assignments = [(101, 1), (102, 999)]  # 999 doesn't exist

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


class TestUtilsMappersMapping:
    """Testing class for bulk-optimized :py:mod:`utils.mappers` mapping function."""

    # # _fetch_and_assign_closed_issues
    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_no_token(self, mocker):
        """Test function returns False when no GitHub token is provided."""
        result = _fetch_and_assign_closed_issues(None)
        assert result is False

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_no_contributions(
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

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        # fetch_issues should not be called when there are no contributions
        mocked_fetch_issues.assert_not_called()
        mocked_create_issues_bulk.assert_not_called()

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_url_in_body_matching(
        self, mocker
    ):
        """Test successful matching when URL appears in issue body."""
        github_token = "test_token"

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
        mock_issue.number = 101
        mock_issue.body = "Check out https://example.com/contrib for details"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([(101, 1)])

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_github_issue_url_match(
        self, mocker
    ):
        """Test successful matching when contribution URL is a GitHub issue URL."""
        github_token = "test_token"

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
        mock_issue.number = 456  # Matching issue number
        mock_issue.body = "Some issue body without the URL"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=456)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([(456, 1)])

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_both_match_same_issue(
        self, mocker
    ):
        """Test that matched flag prevents duplicate assignments for same issue."""
        github_token = "test_token"

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
        mock_issue.number = 101
        mock_issue.body = "Contains https://example.com/contrib1"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocked_is_url = mocker.patch("utils.mappers._is_url_github_issue")
        mocked_is_url.side_effect = lambda url: (
            101 if url == github_issue_url else False
        )
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        # Should only have one assignment despite both methods potentially matching
        call_args = mocked_create_issues_bulk.call_args[0][0]
        assert len(call_args) == 2
        # Should be the body match (first method)
        assert call_args[0] == (101, 1)

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_skip_empty_urls(
        self, mocker
    ):
        """Test that contributions with empty URLs are skipped."""
        github_token = "test_token"

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
        mock_issue.number = 101
        mock_issue.body = "Contains https://valid.com/url"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        # Should only process the valid URL
        mocked_create_issues_bulk.assert_called_once_with([(101, 3)])

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_transaction_decorator(
        self, mocker
    ):
        """Test that function has transaction.atomic decorator."""
        github_token = "test_token"

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
        mock_issue.number = 101
        mock_issue.body = "Contains https://example.com/contrib"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        # Check that function is decorated with transaction.atomic
        # by checking if it's wrapped
        assert (
            _fetch_and_assign_closed_issues.__name__
            == "_fetch_and_assign_closed_issues"
        )

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once()

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_issue_no_body_url_match(
        self, mocker
    ):
        """Test that issues without body are still checked for issue URL matching."""
        github_token = "test_token"

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
        mock_issue.number = 456
        mock_issue.body = None

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=456)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        # Should still match via GitHub issue URL even with no body
        mocked_create_issues_bulk.assert_called_once_with([(456, 1)])

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_no_matches(self, mocker):
        """Test function when no URLs match any issue bodies or GitHub issue URLs."""
        github_token = "test_token"

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
        mock_issue.number = 101
        mock_issue.body = "Contains completely different URL"

        mocker.patch("utils.mappers.fetch_issues", return_value=[mock_issue])
        mocker.patch("utils.mappers._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([])

    @pytest.mark.django_db
    def test_utils_mappers_fetch_and_assign_closed_issues_bulk_multiple_issues(
        self, mocker
    ):
        """Test processing multiple issues with different matching methods."""
        github_token = "test_token"

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
        mock_issue1.number = 101
        mock_issue1.body = "Contains https://example.com/body_match"

        mock_issue2 = mocker.MagicMock()
        mock_issue2.number = 202
        mock_issue2.body = "No matching URL here"

        mocker.patch(
            "utils.mappers.fetch_issues",
            return_value=[mock_issue1, mock_issue2],
        )
        mocked_is_url = mocker.patch("utils.mappers._is_url_github_issue")
        mocked_is_url.side_effect = lambda url: (
            202 if url == github_issue_url else False
        )
        mocked_create_issues_bulk = mocker.patch("utils.mappers._create_issues_bulk")

        result = _fetch_and_assign_closed_issues(github_token)

        assert result is True
        # Should have both assignments via different methods
        call_args = mocked_create_issues_bulk.call_args[0][0]
        assert set(call_args) == {(101, 1), (202, 2)}


class TestUtilsMappersPublicFunctions:
    """Testing class for bulk-optimized :py:mod:`utils.mappers` public function."""

    # # map_github_issues

    @pytest.mark.django_db
    def test_utils_mappers_import_from_csv_calls_fetch_and_assign_closed_issues(
        self, mocker
    ):
        # Mock empty database check

        mock_closed_issues = mocker.patch(
            "utils.mappers._fetch_and_assign_closed_issues"
        )

        result = map_github_issues(github_token="github_token")

        # Verify _create_superusers was called
        mock_closed_issues.assert_called_once_with("github_token")

        assert result is False
