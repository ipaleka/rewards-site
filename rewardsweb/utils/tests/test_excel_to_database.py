"""Testing module for :py:mod:`utils.excel_to_database` module."""

from datetime import datetime, timedelta

import pandas as pd
import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.http import Http404

from core.models import IssueStatus, RewardType
from utils.excel_to_database import (
    REWARDS_COLLECTION,
    _check_current_cycle,
    _create_active_rewards,
    _create_issues_bulk,
    _create_superusers,
    _dataframe_from_csv,
    _fetch_and_assign_issues,
    _import_contributions,
    _import_rewards,
    _is_url_github_issue,
    _parse_addresses,
    _parse_label_and_name_from_reward_type,
    _parse_label_and_name_from_reward_type_legacy,
    _reward_amount,
    _reward_amount_legacy,
    _social_platforms,
    convert_and_clean_excel,
    import_from_csv,
)


class TestUtilsExcelToDatabaseHelperFunctions:
    """Testing class for :py:mod:`utils.excel_to_database` helper functions."""

    # # _check_current_cycle
    def test_utils_excel_to_database_check_current_cycle_creates_new_cycle(
        self, mocker
    ):
        cycle_instance = mocker.MagicMock()
        cycle_instance.end = datetime.now().date() - timedelta(days=1)

        mocked_cycle_create = mocker.patch(
            "utils.excel_to_database.Cycle.objects.create"
        )
        mocked_datetime = mocker.patch("utils.excel_to_database.datetime")
        mocked_datetime.now.return_value.date.return_value = datetime.now().date()

        _check_current_cycle(cycle_instance)

        mocked_cycle_create.assert_called_once()

    def test_utils_excel_to_database_check_current_cycle_no_new_cycle(self, mocker):
        cycle_instance = mocker.MagicMock()
        cycle_instance.end = datetime.now().date() + timedelta(days=1)

        mocked_cycle_create = mocker.patch(
            "utils.excel_to_database.Cycle.objects.create"
        )
        mocked_datetime = mocker.patch("utils.excel_to_database.datetime")
        mocked_datetime.now.return_value.date.return_value = datetime.now().date()

        _check_current_cycle(cycle_instance)

        mocked_cycle_create.assert_not_called()

    # # _create_active_rewards
    def test_utils_excel_to_database_create_active_rewards(self, mocker):
        mocked_get_object_or_404 = mocker.patch(
            "utils.excel_to_database.get_object_or_404"
        )

        rewards = [mocker.MagicMock() for _ in range(len(REWARDS_COLLECTION) * 3)]
        rewards[1] = ObjectDoesNotExist("rwd1")
        rewards[7] = ObjectDoesNotExist("rwd5")
        mocked_reward_get = mocker.patch(
            "utils.excel_to_database.Reward.objects.get", side_effect=rewards
        )
        mocked_reward_create = mocker.patch(
            "utils.excel_to_database.Reward.objects.create"
        )
        reward_type = mocker.MagicMock()
        mocked_get_object_or_404.return_value = reward_type

        _create_active_rewards()

        assert mocked_get_object_or_404.call_count == len(REWARDS_COLLECTION) * 3
        assert mocked_reward_get.call_count == len(REWARDS_COLLECTION) * 3
        calls = [
            mocker.call(type=reward_type, level=2, amount=60000, active=True),
            mocker.call(type=reward_type, level=2, amount=70000, active=True),
        ]
        mocked_reward_create.assert_has_calls(calls, any_order=True)
        assert mocked_reward_create.call_count == 2

    # # _create_superusers
    def test_utils_excel_to_database_create_superusers(self, mocker):
        mocked_get_env_variable = mocker.patch(
            "utils.excel_to_database.get_env_variable"
        )
        mocked_get_env_variable.side_effect = ["user1,user2", "pass1,pass2"]

        mocked_user_create = mocker.patch(
            "utils.excel_to_database.User.objects.create_superuser"
        )

        _create_superusers()

        assert mocked_user_create.call_count == 2
        mocked_user_create.assert_any_call("user1", password="pass1")
        mocked_user_create.assert_any_call("user2", password="pass2")

    # # _dataframe_from_csv
    def test_utils_excel_to_database_dataframe_from_csv_success(self, mocker):
        mock_dataframe = pd.DataFrame(
            {
                "contributor": ["user1", "user2"],
                "cycle_start": ["2023-01-01", "2023-01-01"],
                "cycle_end": ["2023-01-31", "2023-01-31"],
                "platform": ["GitHub", "Discord"],
                "url": ["https://example.com", None],
                "type": ["[F] Feature", "[B] Bug"],
                "level": [1, 2],
                "percentage": [100.0, 50.0],
                "reward": [1000, 500],
                "comment": ["Test comment", None],
            }
        )

        mocked_pd_read_csv = mocker.patch("utils.excel_to_database.pd.read_csv")
        mocked_pd_read_csv.return_value = mock_dataframe

        result = _dataframe_from_csv("test.csv")

        mocked_pd_read_csv.assert_called_once_with("test.csv", header=None, sep=",")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_utils_excel_to_database_dataframe_from_csv_file_not_found(self, mocker):
        mocked_pd_read_csv = mocker.patch("utils.excel_to_database.pd.read_csv")
        mocked_pd_read_csv.side_effect = FileNotFoundError

        result = _dataframe_from_csv("nonexistent.csv")

        assert result is None

    def test_utils_excel_to_database_dataframe_from_csv_empty_data(self, mocker):
        mocked_pd_read_csv = mocker.patch("utils.excel_to_database.pd.read_csv")
        mocked_pd_read_csv.side_effect = pd.errors.EmptyDataError

        result = _dataframe_from_csv("empty.csv")

        assert result is None

    # _import_rewards
    def test_utils_excel_to_database_import_rewards_new_type(self, mocker):
        # Create real DataFrame
        mock_data = pd.DataFrame(
            {"type": ["[F] Feature"], "level": [1], "reward": [1000]}
        )

        mocked_parse_callback = mocker.MagicMock(return_value=("F", "Feature"))
        mocked_amount_callback = mocker.MagicMock(return_value=1000000)
        mocked_get_object_or_404 = mocker.patch(
            "utils.excel_to_database.get_object_or_404"
        )
        mocked_get_object_or_404.side_effect = Http404

        mocked_reward_type_create = mocker.patch(
            "utils.excel_to_database.RewardType.objects.create"
        )
        mocked_reward_create = mocker.patch(
            "utils.excel_to_database.Reward.objects.create"
        )

        _import_rewards(mock_data, mocked_parse_callback, mocked_amount_callback)

        mocked_reward_type_create.assert_called_once_with(label="F", name="Feature")
        mocked_reward_create.assert_called_once()

    def test_utils_excel_to_database_import_rewards_existing_type(self, mocker):
        # Create real DataFrame
        mock_data = pd.DataFrame(
            {"type": ["[F] Feature"], "level": [1], "reward": [1000]}
        )

        mocked_parse_callback = mocker.MagicMock(return_value=("F", "Feature"))
        mocked_amount_callback = mocker.MagicMock(return_value=1000000)
        mocked_reward_type = mocker.MagicMock()

        mocked_get_object_or_404 = mocker.patch(
            "utils.excel_to_database.get_object_or_404"
        )
        mocked_get_object_or_404.return_value = mocked_reward_type

        mocked_reward_create = mocker.patch(
            "utils.excel_to_database.Reward.objects.create"
        )

        _import_rewards(mock_data, mocked_parse_callback, mocked_amount_callback)

        mocked_get_object_or_404.assert_called_once_with(
            RewardType, label="F", name="Feature"
        )
        mocked_reward_create.assert_called_once()

    def test_utils_excel_to_database_import_rewards_for_integrity_error(self, mocker):
        # Create real DataFrame
        mock_data = pd.DataFrame(
            {"type": ["[F] Feature"], "level": [1], "reward": [1000]}
        )

        mocked_parse_callback = mocker.MagicMock(return_value=("F", "Feature"))
        mocked_amount_callback = mocker.MagicMock(return_value=1000000)
        mocked_reward_type = mocker.MagicMock()

        mocked_get_object_or_404 = mocker.patch(
            "utils.excel_to_database.get_object_or_404"
        )
        mocked_get_object_or_404.return_value = mocked_reward_type

        mocker.patch(
            "utils.excel_to_database.Reward.objects.create",
            side_effect=IntegrityError("error"),
        )

        _import_rewards(mock_data, mocked_parse_callback, mocked_amount_callback)

    # # _import_contributions
    def test_utils_excel_to_database_import_contributions(self, mocker):
        # Create real DataFrame
        mock_data = pd.DataFrame(
            [
                {
                    "contributor": "testuser",
                    "cycle_start": "2023-01-01",
                    "platform": "GitHub",
                    "type": "[F] Feature",
                    "level": 1,
                    "reward": 1000,
                    "percentage": 50.0,
                    "url": "https://example.com",
                    "comment": "Test comment",
                }
            ]
        )

        mocked_contributor = mocker.MagicMock()
        mocked_cycle = mocker.MagicMock()
        mocked_platform = mocker.MagicMock()
        mocked_reward_type = mocker.MagicMock()
        mocked_reward = mocker.MagicMock()

        mocked_contributor_from_handle = mocker.patch(
            "utils.excel_to_database.Contributor.objects.from_full_handle"
        )
        mocked_contributor_from_handle.return_value = mocked_contributor

        mocked_cycle_get = mocker.patch("utils.excel_to_database.Cycle.objects.get")
        mocked_cycle_get.return_value = mocked_cycle

        mocked_platform_get = mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.get"
        )
        mocked_platform_get.return_value = mocked_platform

        mocked_parse_callback = mocker.MagicMock(return_value=("F", "Feature"))
        mocked_get_object_or_404 = mocker.patch(
            "utils.excel_to_database.get_object_or_404"
        )
        mocked_get_object_or_404.return_value = mocked_reward_type

        mocked_reward_get = mocker.patch("utils.excel_to_database.Reward.objects.get")
        mocked_reward_get.return_value = mocked_reward

        mocked_amount_callback = mocker.MagicMock(return_value=1000000)
        mocked_contribution_create = mocker.patch(
            "utils.excel_to_database.Contribution.objects.create"
        )

        _import_contributions(mock_data, mocked_parse_callback, mocked_amount_callback)

        mocked_contributor_from_handle.assert_called_once_with("testuser")
        mocked_cycle_get.assert_called_once_with(start="2023-01-01")
        mocked_platform_get.assert_called_once_with(name__iexact="GitHub")
        mocked_parse_callback.assert_called_once_with("[F] Feature")
        mocked_get_object_or_404.assert_called_once_with(
            RewardType, label="F", name="Feature"
        )
        mocked_reward_get.assert_called_once_with(
            type=mocked_reward_type, level=1, amount=1000000
        )
        mocked_contribution_create.assert_called_once()

    # # _is_url_github_issue
    def test_utils_excel_to_database_is_url_github_issue_valid_url(self):
        """Test valid GitHub issue URL returns issue number."""
        valid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/123"
        )

        result = _is_url_github_issue(valid_url)

        assert result == 123

    def test_utils_excel_to_database_is_url_github_issue_invalid_domain(self):
        """Test invalid domain returns False."""
        invalid_url = "https://gitlab.com/owner/repo/issues/123"

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_excel_to_database_is_url_github_issue_invalid_owner(self):
        """Test invalid repo owner returns False."""
        invalid_url = (
            f"https://github.com/wrong_owner/{settings.GITHUB_REPO_NAME}/issues/123"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_excel_to_database_is_url_github_issue_invalid_repo(self):
        """Test invalid repo name returns False."""
        invalid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/wrong_repo/issues/123"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_excel_to_database_is_url_github_issue_invalid_path(self):
        """Test invalid path returns False."""
        invalid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/pulls/123"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    def test_utils_excel_to_database_is_url_github_issue_non_numeric_issue(self):
        """Test non-numeric issue number returns False."""
        invalid_url = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/abc"
        )

        result = _is_url_github_issue(invalid_url)

        assert result is False

    # # _parse_addresses
    def test_utils_excel_to_database_parse_addresses_file_not_found(self, mocker):
        mocked_dataframe_from_csv = mocker.patch(
            "utils.excel_to_database._dataframe_from_csv"
        )
        mocked_dataframe_from_csv.return_value = None

        result = _parse_addresses()

        assert result == []

    def test_utils_excel_to_database_parse_addresses_success(self, mocker):
        # Create a real DataFrame for testing
        test_data = pd.DataFrame(
            {
                "handle": ["handle1", "handle2", "handle3", "handle1"],
                "address": ["addr1", "addr1", "addr2", "addr1"],
            }
        )

        mocked_dataframe_from_csv = mocker.patch(
            "utils.excel_to_database._dataframe_from_csv"
        )
        mocked_dataframe_from_csv.return_value = test_data

        result = _parse_addresses()

        # Expected result after grouping
        expected = [["addr1", ["handle2", "handle1"]], ["addr2", ["handle3"]]]
        assert result == expected

    # # _parse_label_and_name_from_reward_type
    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_standard(
        self,
    ):
        result = _parse_label_and_name_from_reward_type("[F] Feature Request")

        assert result == ("F", "Feature Request")

    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_custom(self):
        result = _parse_label_and_name_from_reward_type("Custom Type")

        assert result == ("CST", "Custom")

    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_nan(self):
        result = _parse_label_and_name_from_reward_type(float("nan"))

        assert result == ("CST", "Custom")

    # # _parse_label_and_name_from_reward_type_legacy
    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_legacy_f(
        self,
    ):
        result = _parse_label_and_name_from_reward_type_legacy("feature request custom")

        assert result == ("F", "Feature Request")

    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_legacy_bug(
        self,
    ):
        result = _parse_label_and_name_from_reward_type_legacy("bug report custom")

        assert result == ("B", "Bug Report")

    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_legacy_r(
        self,
    ):
        result = _parse_label_and_name_from_reward_type_legacy(
            "ecosystem research custom"
        )

        assert result == ("ER", "Ecosystem Research")

    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_legacy_s(
        self,
    ):
        result = _parse_label_and_name_from_reward_type_legacy("something custom")

        assert result == ("S", "Suggestion")

    def test_utils_excel_to_database_parse_label_and_name_from_reward_type_legacy(
        self,
    ):
        result = _parse_label_and_name_from_reward_type_legacy("[F] Feature Request")

        assert result == ("F", "Feature Request")

    # # _reward_amount
    def test_utils_excel_to_database_reward_amount_normal(self):
        result = _reward_amount(1.5)

        assert result == 1500000

    def test_utils_excel_to_database_reward_amount_nan(self):
        result = _reward_amount(float("nan"))

        assert result == 0

    # # _reward_amount_legacy
    def test_utils_excel_to_database_reward_amount_legacy_normal(self):
        result = _reward_amount_legacy(1.5)

        assert result == 1500000

    def test_utils_excel_to_database_reward_amount_legacy_nan(self):
        result = _reward_amount_legacy(float("nan"))

        assert result == 0

    # # _social_platforms
    def test_utils_excel_to_database_social_platforms(self):
        result = _social_platforms()

        expected = [
            ("Discord", ""),
            ("Twitter", "@"),
            ("Reddit", "u/"),
            ("GitHub", "g@"),
            ("Telegram", "t@"),
            ("Forum", "f@"),
        ]
        assert result == expected


class TestUtilsExcelToDatabasePublicFunctions:
    """Testing class for :py:mod:`utils.excel_to_database` main functions."""

    # # import_from_csv
    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_database_not_empty(self, mocker):
        # Mock the exact condition that triggers early return
        # The function checks: if len(SocialPlatform.objects.all()):
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=1)

        # Patch SocialPlatform.objects.all to return our mock with length 1
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Call the function - it should return early with error message
        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify the function returned early with error message
        assert result == "ERROR: Database is not empty!"

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_success(self, mocker):
        # Mock empty database check - return empty queryset
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock all dependencies with proper return values
        mocker.patch(
            "utils.excel_to_database._social_platforms",
            return_value=[("Discord", ""), ("GitHub", "g@")],
        )
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")

        # Mock addresses parsing
        mocker.patch(
            "utils.excel_to_database._parse_addresses",
            return_value=[("ADDRESS1", "handle1"), ("ADDRESS2", "handle2")],
        )

        # Mock Contributor creation
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")

        # Mock Handle creation completely to avoid database issues
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Mock DataFrame creation with real DataFrames
        mock_data = pd.DataFrame(
            {
                "contributor": ["user1"],
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "platform": ["GitHub"],
                "url": ["https://example.com"],
                "type": ["[F] Feature"],
                "level": [1],
                "percentage": [100.0],
                "reward": [1000],
                "comment": ["Test comment"],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "contributor": ["user2"],
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "platform": ["Discord"],
                "url": [None],
                "type": ["[B] Bug"],
                "level": [2],
                "percentage": [50.0],
                "reward": [500],
                "comment": [None],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")

        mock_latest_cycle = mocker.MagicMock()
        mock_latest_cycle.end = datetime.now().date() + timedelta(days=1)
        mocker.patch(
            "utils.excel_to_database.Cycle.objects.latest",
            return_value=mock_latest_cycle,
        )

        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")

        result = import_from_csv("contributions.csv", "legacy.csv")

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_saves_handles(self, mocker):
        # Mock empty database check - return empty queryset
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock all dependencies with proper return values
        mocker.patch(
            "utils.excel_to_database._social_platforms",
            return_value=[("Discord", ""), ("GitHub", "g@")],
        )
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")

        # Mock addresses parsing
        mocker.patch(
            "utils.excel_to_database._parse_addresses",
            return_value=[
                ("ADDRESS1", ["handle1", "handle1b"]),
                ("ADDRESS2", ["handle2"]),
            ],
        )

        # Mock Contributor creation
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")

        # Mock Handle creation completely to avoid database issues
        handle1, handle2, handle3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mocked_handle = mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle",
            side_effect=[handle1, handle2, handle3],
        )

        # Mock DataFrame creation with real DataFrames
        mock_data = pd.DataFrame(
            {
                "contributor": ["user1"],
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "platform": ["GitHub"],
                "url": ["https://example.com"],
                "type": ["[F] Feature"],
                "level": [1],
                "percentage": [100.0],
                "reward": [1000],
                "comment": ["Test comment"],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "contributor": ["user2"],
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "platform": ["Discord"],
                "url": [None],
                "type": ["[B] Bug"],
                "level": [2],
                "percentage": [50.0],
                "reward": [500],
                "comment": [None],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")

        mock_latest_cycle = mocker.MagicMock()
        mock_latest_cycle.end = datetime.now().date() + timedelta(days=1)
        mocker.patch(
            "utils.excel_to_database.Cycle.objects.latest",
            return_value=mock_latest_cycle,
        )

        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")
        mocker.patch("utils.excel_to_database._fetch_and_assign_issues")

        result = import_from_csv("contributions.csv", "legacy.csv")

        calls = [
            mocker.call("ADDRESS1", "handle1"),
            mocker.call("ADDRESS1", "handle1b"),
            mocker.call("ADDRESS2", "handle2"),
        ]
        mocked_handle.assert_has_calls(calls, any_order=True)
        assert mocked_handle.call_count == 3
        handle1.save.assert_called_once_with()
        handle2.save.assert_called_once_with()
        handle3.save.assert_called_once_with()

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_creates_social_platforms(
        self, mocker
    ):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock social platforms data
        mock_platforms_data = [("Discord", ""), ("GitHub", "g@"), ("Twitter", "t@")]
        mocker.patch(
            "utils.excel_to_database._social_platforms",
            return_value=mock_platforms_data,
        )

        # Mock bulk_create to capture what's being created
        mock_bulk_create = mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.bulk_create"
        )

        # Create proper mock DataFrames with all required columns
        mock_data = pd.DataFrame(
            {
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "type": ["[F] Feature"],
                "level": [1],
                "reward": [1000],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "type": ["[B] Bug"],
                "level": [2],
                "reward": [500],
            }
        )

        # Mock other dependencies minimally
        mocker.patch("utils.excel_to_database._parse_addresses", return_value=[])
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )
        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")
        mocker.patch("utils.excel_to_database.Cycle.objects.latest")
        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")
        mocker.patch("utils.excel_to_database._fetch_and_assign_issues")

        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify SocialPlatform.objects.bulk_create was called with the correct generator
        mock_bulk_create.assert_called_once()
        call_args = mock_bulk_create.call_args[0][
            0
        ]  # Get the generator passed to bulk_create
        created_platforms = list(call_args)  # Convert generator to list to inspect

        assert len(created_platforms) == len(mock_platforms_data)
        for i, (name, prefix) in enumerate(mock_platforms_data):
            assert created_platforms[i].name == name
            assert created_platforms[i].prefix == prefix

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_creates_contributors(self, mocker):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock platforms
        mocker.patch(
            "utils.excel_to_database._social_platforms",
            return_value=[("Discord", ""), ("GitHub", "g@")],
        )
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")

        # Mock addresses parsing with multiple contributors
        mock_addresses = [
            ("0x1234567890abcdef", ["alice", "alice_gh"]),
            ("0xfedcba0987654321", ["bob"]),
            ("0xabcdef1234567890", ["charlie", "charlie_discord", "charlie_twitter"]),
        ]
        mocker.patch(
            "utils.excel_to_database._parse_addresses",
            return_value=mock_addresses,
        )

        # Mock Contributor bulk_create to capture what's being created
        mock_contributor_bulk_create = mocker.patch(
            "utils.excel_to_database.Contributor.objects.bulk_create"
        )

        # Mock Handle creation
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Create proper mock DataFrames with all required columns
        mock_data = pd.DataFrame(
            {
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "type": ["[F] Feature"],
                "level": [1],
                "reward": [1000],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "type": ["[B] Bug"],
                "level": [2],
                "reward": [500],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")
        mocker.patch("utils.excel_to_database.Cycle.objects.latest")
        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")
        mocker.patch("utils.excel_to_database._fetch_and_assign_issues")

        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify Contributor.objects.bulk_create was called with the correct generator
        mock_contributor_bulk_create.assert_called_once()
        call_args = mock_contributor_bulk_create.call_args[0][0]
        created_contributors = list(call_args)

        assert len(created_contributors) == len(mock_addresses)
        for i, (address, handles) in enumerate(mock_addresses):
            assert created_contributors[i].address == address
            assert (
                created_contributors[i].name == handles[0]
            )  # First handle is used as name

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_creates_cycles(self, mocker):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock basic dependencies
        mocker.patch("utils.excel_to_database._social_platforms")
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")
        mocker.patch("utils.excel_to_database._parse_addresses", return_value=[])
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Mock DataFrame creation with cycle data - include all required columns
        mock_data = pd.DataFrame(
            {
                "cycle_start": ["2023-01-01", "2023-02-01"],
                "cycle_end": ["2023-01-31", "2023-02-28"],
                "type": ["[F] Feature", "[B] Bug"],
                "level": [1, 2],
                "reward": [1000, 500],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "type": ["[F] Feature"],
                "level": [1],
                "reward": [800],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        # Mock Cycle bulk_create to capture what's being created
        mock_cycle_bulk_create = mocker.patch(
            "utils.excel_to_database.Cycle.objects.bulk_create"
        )

        # Mock latest cycle check
        mock_latest_cycle = mocker.MagicMock()
        mock_latest_cycle.end = datetime.now().date() + timedelta(days=1)
        mocker.patch(
            "utils.excel_to_database.Cycle.objects.latest",
            return_value=mock_latest_cycle,
        )
        mock_check_current_cycle = mocker.patch(
            "utils.excel_to_database._check_current_cycle"
        )

        # Mock remaining dependencies
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")
        mocker.patch("utils.excel_to_database._fetch_and_assign_issues")

        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify Cycle.objects.bulk_create was called with the correct cycles
        mock_cycle_bulk_create.assert_called_once()
        call_args = mock_cycle_bulk_create.call_args[0][0]
        created_cycles = list(call_args)

        # Should have 3 unique cycles (2 from mock_data, 1 from mock_legacy_data)
        expected_cycles = [
            ("2022-12-01", "2022-12-31"),
            ("2023-01-01", "2023-01-31"),
            ("2023-02-01", "2023-02-28"),
        ]

        assert len(created_cycles) == len(expected_cycles)
        for i, (start, end) in enumerate(expected_cycles):
            assert str(created_cycles[i].start) == start
            assert str(created_cycles[i].end) == end

        # Verify _check_current_cycle was called with the latest cycle
        mock_check_current_cycle.assert_called_once_with(mock_latest_cycle)

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_calls_reward_functions(
        self, mocker
    ):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock basic dependencies
        mocker.patch("utils.excel_to_database._social_platforms")
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")
        mocker.patch("utils.excel_to_database._parse_addresses", return_value=[])
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Mock DataFrame creation with all required columns
        mock_data = pd.DataFrame(
            {
                "type": ["[F] Feature"],
                "level": [1],
                "reward": [1000],
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "type": ["[B] Bug"],
                "level": [2],
                "reward": [500],
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")
        mocker.patch("utils.excel_to_database.Cycle.objects.latest")
        mocker.patch("utils.excel_to_database._check_current_cycle")

        # Mock reward functions to verify they're called correctly
        mock_import_rewards = mocker.patch("utils.excel_to_database._import_rewards")
        mock_create_active_rewards = mocker.patch(
            "utils.excel_to_database._create_active_rewards"
        )
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")
        mocker.patch("utils.excel_to_database._fetch_and_assign_issues")

        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify _import_rewards was called twice with correct parameters
        assert mock_import_rewards.call_count == 2

        # First call for current data
        first_call_args = mock_import_rewards.call_args_list[0]
        pd.testing.assert_frame_equal(
            first_call_args[0][0], mock_data[["type", "level", "reward"]]
        )
        assert first_call_args[0][1] == _parse_label_and_name_from_reward_type
        assert first_call_args[0][2] == _reward_amount

        # Second call for legacy data
        second_call_args = mock_import_rewards.call_args_list[1]
        pd.testing.assert_frame_equal(
            second_call_args[0][0], mock_legacy_data[["type", "level", "reward"]]
        )
        assert second_call_args[0][1] == _parse_label_and_name_from_reward_type_legacy
        assert second_call_args[0][2] == _reward_amount_legacy

        # Verify _create_active_rewards was called
        mock_create_active_rewards.assert_called_once_with()

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_calls_contribution_functions(
        self, mocker
    ):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock basic dependencies
        mocker.patch("utils.excel_to_database._social_platforms")
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")
        mocker.patch("utils.excel_to_database._parse_addresses", return_value=[])
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Mock DataFrame creation with all required columns
        mock_data = pd.DataFrame(
            {
                "contributor": ["user1"],
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "platform": ["GitHub"],
                "url": ["https://example.com"],
                "type": ["[F] Feature"],
                "level": [1],
                "percentage": [100.0],
                "reward": [1000],
                "comment": ["Test comment"],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "contributor": ["user2"],
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "platform": ["Discord"],
                "url": [None],
                "type": ["[B] Bug"],
                "level": [2],
                "percentage": [50.0],
                "reward": [500],
                "comment": [None],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")
        mocker.patch("utils.excel_to_database.Cycle.objects.latest")
        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")

        # Mock contribution functions to verify they're called correctly
        mock_import_contributions = mocker.patch(
            "utils.excel_to_database._import_contributions"
        )
        mocker.patch("utils.excel_to_database._create_superusers")
        mocker.patch("utils.excel_to_database._fetch_and_assign_issues")

        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify _import_contributions was called twice with correct parameters
        assert mock_import_contributions.call_count == 2

        # First call for legacy data (called first in the function)
        first_call_args = mock_import_contributions.call_args_list[0]
        pd.testing.assert_frame_equal(first_call_args[0][0], mock_legacy_data)
        assert first_call_args[0][1] == _parse_label_and_name_from_reward_type_legacy
        assert first_call_args[0][2] == _reward_amount_legacy

        # Second call for current data
        second_call_args = mock_import_contributions.call_args_list[1]
        pd.testing.assert_frame_equal(second_call_args[0][0], mock_data)
        assert second_call_args[0][1] == _parse_label_and_name_from_reward_type
        assert second_call_args[0][2] == _reward_amount

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_calls__fetch_and_assign_issues(
        self, mocker
    ):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock all dependencies minimally
        mocker.patch("utils.excel_to_database._social_platforms")
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")
        mocker.patch("utils.excel_to_database._parse_addresses", return_value=[])
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Create proper mock DataFrames with all required columns
        mock_data = pd.DataFrame(
            {
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "type": ["[F] Feature"],
                "level": [1],
                "reward": [1000],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "type": ["[B] Bug"],
                "level": [2],
                "reward": [500],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")
        mocker.patch("utils.excel_to_database.Cycle.objects.latest")
        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")
        mocker.patch("utils.excel_to_database._create_superusers")
        mock_fetch_issues = mocker.patch(
            "utils.excel_to_database._fetch_and_assign_issues"
        )

        result = import_from_csv(
            "contributions.csv", "legacy.csv", github_token="github_token"
        )

        # Verify _create_superusers was called
        mock_fetch_issues.assert_called_once_with("github_token")

        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_calls_create_superusers(
        self, mocker
    ):
        # Mock empty database check
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=0)
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        # Mock all dependencies minimally
        mocker.patch("utils.excel_to_database._social_platforms")
        mocker.patch("utils.excel_to_database.SocialPlatform.objects.bulk_create")
        mocker.patch("utils.excel_to_database._parse_addresses", return_value=[])
        mocker.patch("utils.excel_to_database.Contributor.objects.bulk_create")
        mocker.patch(
            "utils.excel_to_database.Handle.objects.from_address_and_full_handle"
        )

        # Create proper mock DataFrames with all required columns
        mock_data = pd.DataFrame(
            {
                "cycle_start": ["2023-01-01"],
                "cycle_end": ["2023-01-31"],
                "type": ["[F] Feature"],
                "level": [1],
                "reward": [1000],
            }
        )
        mock_legacy_data = pd.DataFrame(
            {
                "cycle_start": ["2022-12-01"],
                "cycle_end": ["2022-12-31"],
                "type": ["[B] Bug"],
                "level": [2],
                "reward": [500],
            }
        )
        mocker.patch(
            "utils.excel_to_database._dataframe_from_csv",
            side_effect=[mock_data, mock_legacy_data],
        )

        mocker.patch("utils.excel_to_database.Cycle.objects.bulk_create")
        mocker.patch("utils.excel_to_database.Cycle.objects.latest")
        mocker.patch("utils.excel_to_database._check_current_cycle")
        mocker.patch("utils.excel_to_database._import_rewards")
        mocker.patch("utils.excel_to_database._create_active_rewards")
        mocker.patch("utils.excel_to_database._import_contributions")

        # Mock _create_superusers to verify it's called
        mock_create_superusers = mocker.patch(
            "utils.excel_to_database._create_superusers"
        )

        result = import_from_csv("contributions.csv", "legacy.csv")

        # Verify _create_superusers was called
        mock_create_superusers.assert_called_once_with()

        assert result is False

    # # convert_and_clean_excel
    def test_utils_excel_to_database_convert_and_clean_excel(self, mocker):
        # Mock the entire pandas read operation chain
        mock_df = mocker.MagicMock()

        # Mock pd.read_excel and all subsequent operations
        mocker.patch(
            "utils.excel_to_database.pd.read_excel"
        ).return_value.iloc.return_value = mock_df
        mock_df.fillna.return_value.infer_objects.return_value = mock_df
        mock_df.drop.return_value = mock_df
        mock_df.__getitem__.return_value = mock_df
        mock_df.map.return_value = mock_df
        mock_df.loc.__getitem__.return_value = mock_df

        # Mock the DataFrame slicing operations
        mock_df.iloc.__getitem__.return_value = mock_df

        # Mock pd.concat to avoid real DataFrame operations
        mocker.patch("utils.excel_to_database.pd.concat", return_value=mock_df)

        # Mock Path operations
        mocker.patch(
            "utils.excel_to_database.Path"
        ).return_value.resolve.return_value.parent.parent.__truediv__.return_value.to_csv = (
            mocker.MagicMock()
        )

        # Mock the final to_csv calls
        mock_df.to_csv = mocker.MagicMock()
        mock_df.iloc.__getitem__.return_value.to_csv = mocker.MagicMock()

        convert_and_clean_excel("input.xlsx", "output.csv", "legacy.csv")

        # Verify the function completed
        assert mock_df.to_csv.called


class TestUtilsExcelToDatabaseCreateIssuesBulk:
    """Testing class for :py:mod:`utils.excel_to_database` _create_issues_bulk function."""

    # # _create_issues_bulk
    def test_utils_excel_to_database_create_issues_bulk_empty_assignments(self, mocker):
        """Test function returns early when no assignments provided."""
        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )
        mocked_contribution_filter = mocker.patch(
            "utils.excel_to_database.Contribution.objects.filter"
        )

        _create_issues_bulk([])

        mocked_issue_filter.assert_not_called()
        mocked_bulk_create.assert_not_called()
        mocked_contribution_filter.assert_not_called()

    @pytest.mark.django_db
    def test_utils_excel_to_database_create_issues_bulk_all_new_issues(self, mocker):
        """Test bulk creation when all issues are new."""
        issue_assignments = [(101, 1), (102, 2), (103, 3)]

        # Create proper QuerySet-like mock for existing issues
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []

        # Mock Issue.objects.filter to return our mock QuerySet
        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )

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

        # Create a proper mock for the contributions queryset that can be converted to list
        mock_contrib_queryset = mocker.MagicMock()
        mock_contrib_queryset.__iter__ = mocker.MagicMock(
            return_value=iter([mock_contrib1, mock_contrib2, mock_contrib3])
        )

        # Mock the filter to return our queryset
        mocked_contrib_filter = mocker.patch(
            "utils.excel_to_database.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        # Mock bulk_update - we need to check it's called with the queryset, not the list
        mocked_bulk_update = mocker.patch(
            "utils.excel_to_database.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Verify issue creation
        mocked_bulk_create.assert_called_once()
        created_issues = mocked_bulk_create.call_args[0][0]
        assert len(created_issues) == 3
        assert {issue.number for issue in created_issues} == {101, 102, 103}
        assert all(issue.status == IssueStatus.ARCHIVED for issue in created_issues)

        # Verify contribution updates - bulk_update is called with the queryset, not the list
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contributions were updated
        assert mock_contrib1.issue == mock_issue1
        assert mock_contrib2.issue == mock_issue2
        assert mock_contrib3.issue == mock_issue3

    @pytest.mark.django_db
    def test_utils_excel_to_database_create_issues_bulk_mixed_existing_issues(
        self, mocker
    ):
        """Test bulk creation when some issues exist and some are new."""
        issue_assignments = [(101, 1), (102, 2)]

        # Mock existing issues (only 101 exists)
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = [101]

        # Mock Issue.objects.filter
        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )

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
            "utils.excel_to_database.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.excel_to_database.Contribution.objects.bulk_update"
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
    def test_utils_excel_to_database_create_issues_bulk_all_existing_issues(
        self, mocker
    ):
        """Test bulk creation when all issues already exist."""
        issue_assignments = [(101, 1), (102, 2)]

        # Mock existing issues (both exist)
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = [101, 102]

        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )

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
            "utils.excel_to_database.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.excel_to_database.Contribution.objects.bulk_update"
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
    def test_utils_excel_to_database_create_issues_bulk_duplicate_assignments(
        self, mocker
    ):
        """Test bulk creation handles duplicate assignments gracefully."""
        issue_assignments = [(101, 1), (101, 1), (102, 2)]  # Duplicate (101, 1)

        # Mock existing issues
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []
        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_issue_filter.return_value = mock_existing_issues

        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )

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
            "utils.excel_to_database.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.excel_to_database.Contribution.objects.bulk_update"
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
    def test_utils_excel_to_database_create_issues_bulk_missing_issue_after_creation(
        self, mocker
    ):
        """Test handling when issue is missing after bulk creation."""
        issue_assignments = [(101, 1)]

        # Mock existing issues (none exist)
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []
        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_issue_filter.return_value = mock_existing_issues

        # Mock bulk create
        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )

        # Mock getting all issues after creation returns empty (shouldn't happen but test robustness)
        mock_empty_queryset = mocker.MagicMock()
        mock_empty_queryset.__iter__ = mocker.MagicMock(return_value=iter([]))
        mocked_issue_filter.side_effect = [mock_existing_issues, mock_empty_queryset]

        # Mock contributions
        mocked_contrib_filter = mocker.patch(
            "utils.excel_to_database.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_empty_queryset

        mocked_bulk_update = mocker.patch(
            "utils.excel_to_database.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Issue should be created
        mocked_bulk_create.assert_called_once()
        # But no contributions should be updated since issue is missing
        mocked_bulk_update.assert_not_called()

    @pytest.mark.django_db
    def test_utils_excel_to_database_create_issues_bulk_no_contributions_found(
        self, mocker
    ):
        """Test handling when no contributions are found for update."""
        issue_assignments = [(101, 1), (102, 999)]  # 999 doesn't exist

        # Mock existing issues
        mock_existing_issues = mocker.MagicMock()
        mock_existing_issues.values_list.return_value = []
        mocked_issue_filter = mocker.patch(
            "utils.excel_to_database.Issue.objects.filter"
        )
        mocked_issue_filter.return_value = mock_existing_issues

        mocked_bulk_create = mocker.patch(
            "utils.excel_to_database.Issue.objects.bulk_create"
        )

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
            "utils.excel_to_database.Contribution.objects.filter"
        )
        mocked_contrib_filter.return_value = mock_contrib_queryset

        mocked_bulk_update = mocker.patch(
            "utils.excel_to_database.Contribution.objects.bulk_update"
        )

        _create_issues_bulk(issue_assignments)

        # Issues should be created
        mocked_bulk_create.assert_called_once()
        # Only existing contribution should be updated - called with queryset
        mocked_bulk_update.assert_called_once_with(mock_contrib_queryset, ["issue"])

        # Verify individual contribution was updated
        assert mock_contrib1.issue == mock_issue1


class TestUtilsExcelToDatabaseFetchAndAssignIssuesBulk:
    """Testing class for bulk-optimized :py:mod:`utils.excel_to_database` _fetch_and_assign_issues function."""

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_no_token(
        self, mocker
    ):
        """Test function returns False when no GitHub token is provided."""
        result = _fetch_and_assign_issues(None)
        assert result is False

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_no_contributions(
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mocked_all_issues = mocker.patch("utils.excel_to_database.all_issues")
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        # all_issues should not be called when there are no contributions
        mocked_all_issues.assert_not_called()
        mocked_create_issues_bulk.assert_not_called()

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_url_in_body_matching(
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue with URL in body
        mock_issue = mocker.MagicMock()
        mock_issue.number = 101
        mock_issue.body = "Check out https://example.com/contrib for details"

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocker.patch("utils.excel_to_database._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([(101, 1)])

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_github_issue_url_matching(
        self, mocker
    ):
        """Test successful matching when contribution URL is a GitHub issue URL."""
        github_token = "test_token"

        # Mock contribution with GitHub issue URL
        github_issue_url = f"https://github.com/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues/456"
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue
        mock_issue = mocker.MagicMock()
        mock_issue.number = 456  # Matching issue number
        mock_issue.body = "Some issue body without the URL"

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocker.patch("utils.excel_to_database._is_url_github_issue", return_value=456)
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([(456, 1)])

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_both_matching_methods_same_issue(
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
        github_issue_url = f"https://github.com/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues/101"
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue that matches both methods
        mock_issue = mocker.MagicMock()
        mock_issue.number = 101
        mock_issue.body = "Contains https://example.com/contrib1"

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocked_is_url = mocker.patch("utils.excel_to_database._is_url_github_issue")
        mocked_is_url.side_effect = lambda url: (
            101 if url == github_issue_url else False
        )
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        # Should only have one assignment despite both methods potentially matching
        call_args = mocked_create_issues_bulk.call_args[0][0]
        assert len(call_args) == 2
        # Should be the body match (first method)
        assert call_args[0] == (101, 1)

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_skip_empty_urls(
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mock_issue = mocker.MagicMock()
        mock_issue.number = 101
        mock_issue.body = "Contains https://valid.com/url"

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocker.patch("utils.excel_to_database._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        # Should only process the valid URL
        mocked_create_issues_bulk.assert_called_once_with([(101, 3)])

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_transaction_decorator(
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mock_issue = mocker.MagicMock()
        mock_issue.number = 101
        mock_issue.body = "Contains https://example.com/contrib"

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocker.patch("utils.excel_to_database._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        # Check that function is decorated with transaction.atomic
        # by checking if it's wrapped
        assert _fetch_and_assign_issues.__name__ == "_fetch_and_assign_issues"

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once()

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_issue_without_body_github_url_match(
        self, mocker
    ):
        """Test that issues without body are still checked for GitHub issue URL matching."""
        github_token = "test_token"

        # Mock contribution with GitHub issue URL
        github_issue_url = f"https://github.com/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues/456"
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        # Mock GitHub issue without body but with matching number
        mock_issue = mocker.MagicMock()
        mock_issue.number = 456
        mock_issue.body = None

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocker.patch("utils.excel_to_database._is_url_github_issue", return_value=456)
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        # Should still match via GitHub issue URL even with no body
        mocked_create_issues_bulk.assert_called_once_with([(456, 1)])

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_no_matches(
        self, mocker
    ):
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
            "utils.excel_to_database.Contribution.objects.all",
            return_value=mock_contributions_queryset,
        )

        mock_issue = mocker.MagicMock()
        mock_issue.number = 101
        mock_issue.body = "Contains completely different URL"

        mocker.patch("utils.excel_to_database.all_issues", return_value=[mock_issue])
        mocker.patch("utils.excel_to_database._is_url_github_issue", return_value=False)
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        mocked_create_issues_bulk.assert_called_once_with([])

    @pytest.mark.django_db
    def test_utils_excel_to_database_fetch_and_assign_issues_bulk_multiple_issues_different_matches(
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
        github_issue_url = f"https://github.com/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues/202"
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
            "utils.excel_to_database.Contribution.objects.all",
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
            "utils.excel_to_database.all_issues",
            return_value=[mock_issue1, mock_issue2],
        )
        mocked_is_url = mocker.patch("utils.excel_to_database._is_url_github_issue")
        mocked_is_url.side_effect = lambda url: (
            202 if url == github_issue_url else False
        )
        mocked_create_issues_bulk = mocker.patch(
            "utils.excel_to_database._create_issues_bulk"
        )

        result = _fetch_and_assign_issues(github_token)

        assert result is True
        # Should have both assignments via different methods
        call_args = mocked_create_issues_bulk.call_args[0][0]
        assert set(call_args) == {(101, 1), (202, 2)}
