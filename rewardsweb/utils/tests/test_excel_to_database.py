"""Testing module for :py:mod:`utils.excel_to_database` module."""

from datetime import datetime, timedelta

import pandas as pd
import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.http import Http404

from core.models import RewardType
from utils.excel_to_database import (
    REWARDS_COLLECTION,
    _check_current_cycle,
    _create_active_rewards,
    _create_superusers,
    _dataframe_from_csv,
    _import_contributions,
    _import_rewards,
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


class TestUtilsExcelToDatabaseImportFunctions:
    """Testing class for :py:mod:`utils.excel_to_database` import functions."""

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


# utils/tests/test_excel_to_database.py


class TestUtilsExcelToDatabasePublicFunctions:
    """Testing class for :py:mod:`utils.excel_to_database` main functions."""

    @pytest.mark.django_db
    def test_utils_excel_to_database_import_from_csv_database_not_empty(self, mocker):
        # Mock non-empty database check - return non-empty queryset
        mock_social_platforms = mocker.MagicMock()
        mock_social_platforms.__len__ = mocker.MagicMock(return_value=5)  # Non-empty
        mocker.patch(
            "utils.excel_to_database.SocialPlatform.objects.all",
            return_value=mock_social_platforms,
        )

        result = import_from_csv("contributions.csv", "legacy.csv")

        assert result == "ERROR: Database is not empty!"

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
