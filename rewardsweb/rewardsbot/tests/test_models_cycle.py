"""Unit tests for :py:mod:`rewardsbot.models.cycle` module.

This module contains tests for the Cycle class and its
formatting functionality.
"""

from datetime import datetime

import pytest

from rewardsbot.models.cycle import Cycle, confirmed_status


class TestModelsCycle:
    """Testing class for :py:mod:`rewardsbot.models.cycle` components."""

    # # confirmed_status function
    def test_models_cycle_confirmed_status_confirmed(self):
        """Test confirmed_status returns checkmark for True."""
        result = confirmed_status(True)
        assert result == "✅"

    def test_models_cycle_confirmed_status_unconfirmed(self):
        """Test confirmed_status returns cross mark for False."""
        result = confirmed_status(False)
        assert result == "⍻"

    # # Cycle initialization
    def test_models_cycle_initialization_with_full_data(self):
        """Test Cycle initialization with complete data."""
        data = {
            "id": 5,
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59",
            "contributor_rewards": {
                "user1": (1000, True),
                "user2": (1500, False),
                "user3": (2000, True),
            },
            "total_rewards": 4500,
        }
        cycle = Cycle(data)

        assert cycle.id == 5
        assert cycle.start == datetime(2024, 1, 1, 0, 0, 0)
        assert cycle.end == datetime(2024, 1, 31, 23, 59, 59)
        assert cycle.contributor_rewards == {
            "user1": (1000, True),
            "user2": (1500, False),
            "user3": (2000, True),
        }
        assert cycle.total_rewards == 4500

    def test_models_cycle_initialization_with_minimal_data(self):
        """Test Cycle initialization with minimal required data."""
        data = {
            "id": 1,
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59",
        }
        cycle = Cycle(data)

        assert cycle.id == 1
        assert cycle.start == datetime(2024, 1, 1, 0, 0, 0)
        assert cycle.end == datetime(2024, 1, 31, 23, 59, 59)
        assert cycle.contributor_rewards == {}
        assert cycle.total_rewards == 0

    def test_models_cycle_initialization_with_empty_contributor_rewards(self):
        """Test Cycle initialization with empty contributor rewards."""
        data = {
            "id": 2,
            "start": "2024-02-01T00:00:00",
            "end": "2024-02-29T23:59:59",
            "contributor_rewards": {},
            "total_rewards": 0,
        }
        cycle = Cycle(data)

        assert cycle.id == 2
        assert cycle.contributor_rewards == {}
        assert cycle.total_rewards == 0

    def test_models_cycle_initialization_with_missing_start_date(self):
        """Test Cycle initialization raises error with missing start date."""
        data = {
            "id": 3,
            "start": None,
            "end": "2024-01-31T23:59:59",
        }

        with pytest.raises(ValueError, match="Start and end dates are required"):
            Cycle(data)

    def test_models_cycle_initialization_with_missing_end_date(self):
        """Test Cycle initialization raises error with missing end date."""
        data = {
            "id": 3,
            "start": "2024-01-01T00:00:00",
            "end": None,
        }

        with pytest.raises(ValueError, match="Start and end dates are required"):
            Cycle(data)

    def test_models_cycle_initialization_with_empty_start_date(self):
        """Test Cycle initialization raises error with empty start date."""
        data = {
            "id": 3,
            "start": "",
            "end": "2024-01-31T23:59:59",
        }

        with pytest.raises(ValueError, match="Start and end dates are required"):
            Cycle(data)

    def test_models_cycle_initialization_with_invalid_date_format(self):
        """Test Cycle initialization raises error with invalid date format."""
        data = {
            "id": 4,
            "start": "invalid-date",
            "end": "2024-01-31T23:59:59",
        }

        with pytest.raises(ValueError, match="Invalid date format"):
            Cycle(data)

    # # Cycle.formatted_cycle_info - current cycle
    def test_models_cycle_formatted_cycle_info_current_with_rewards(self):
        """Test formatted_cycle_info for current cycle with rewards."""
        data = {
            "id": 5,
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59",
            "contributor_rewards": {
                "Alice": (1000, True),
                "Bob": (1500, False),
                "Charlie": (2000, True),
            },
            "total_rewards": 4500,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        expected_lines = [
            "The current cycle #5 started on 2024-01-01 and ends on 2024-01-31",
            "",
            "**Contributors & Rewards:**",
            "",
            "Alice 1,000 ✅",
            "Bob 1,500 ⍻",
            "Charlie 2,000 ✅",
            "",
            "Cycle total: 4,500",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_models_cycle_formatted_cycle_info_current_empty_rewards(self):
        """Test formatted_cycle_info for current cycle with no rewards."""
        data = {
            "id": 6,
            "start": "2024-02-01T00:00:00",
            "end": "2024-02-29T23:59:59",
            "contributor_rewards": {},
            "total_rewards": 0,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        expected_lines = [
            "The current cycle #6 started on 2024-02-01 and ends on 2024-02-29",
            "",
            "**Contributors & Rewards:**",
            "",
            "No contributors yet",
            "",
            "Cycle total: 0",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_models_cycle_formatted_cycle_info_current_single_reward(self):
        """Test formatted_cycle_info for current cycle with single reward."""
        data = {
            "id": 7,
            "start": "2024-03-01T00:00:00",
            "end": "2024-03-31T23:59:59",
            "contributor_rewards": {
                "SoloContributor": (5000, True),
            },
            "total_rewards": 5000,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        expected_lines = [
            "The current cycle #7 started on 2024-03-01 and ends on 2024-03-31",
            "",
            "**Contributors & Rewards:**",
            "",
            "SoloContributor 5,000 ✅",
            "",
            "Cycle total: 5,000",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    # # Cycle.formatted_cycle_info - past cycle
    def test_models_cycle_formatted_cycle_info_past_with_rewards(self):
        """Test formatted_cycle_info for past cycle with rewards."""
        data = {
            "id": 4,
            "start": "2023-12-01T00:00:00",
            "end": "2023-12-31T23:59:59",
            "contributor_rewards": {
                "UserA": (1200, True),
                "UserB": (1800, True),
            },
            "total_rewards": 3000,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=False)

        expected_lines = [
            "The cycle #4 started on 2023-12-01 and ended on 2023-12-31",
            "",
            "**Contributors & Rewards:**",
            "",
            "UserA 1,200 ✅",
            "UserB 1,800 ✅",
            "",
            "Cycle total: 3,000",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_models_cycle_formatted_cycle_info_past_empty_rewards(self):
        """Test formatted_cycle_info for past cycle with no rewards."""
        data = {
            "id": 3,
            "start": "2023-11-01T00:00:00",
            "end": "2023-11-30T23:59:59",
            "contributor_rewards": {},
            "total_rewards": 0,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=False)

        expected_lines = [
            "The cycle #3 started on 2023-11-01 and ended on 2023-11-30",
            "",
            "**Contributors & Rewards:**",
            "",
            "No contributors yet",
            "",
            "Cycle total: 0",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    # # Cycle.formatted_cycle_info - edge cases
    def test_models_cycle_formatted_cycle_info_large_reward_numbers(self):
        """Test formatted_cycle_info with large reward numbers."""
        data = {
            "id": 8,
            "start": "2024-04-01T00:00:00",
            "end": "2024-04-30T23:59:59",
            "contributor_rewards": {
                "BigContributor": (1000000, True),
                "MediumContributor": (500000, False),
                "SmallContributor": (1000, True),
            },
            "total_rewards": 1501000,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        expected_lines = [
            "The current cycle #8 started on 2024-04-01 and ends on 2024-04-30",
            "",
            "**Contributors & Rewards:**",
            "",
            "BigContributor 1,000,000 ✅",
            "MediumContributor 500,000 ⍻",
            "SmallContributor 1,000 ✅",
            "",
            "Cycle total: 1,501,000",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_models_cycle_formatted_cycle_info_mixed_confirmation_status(self):
        """Test formatted_cycle_info with mixed confirmation statuses."""
        data = {
            "id": 9,
            "start": "2024-05-01T00:00:00",
            "end": "2024-05-31T23:59:59",
            "contributor_rewards": {
                "ConfirmedOnly": (1000, True),
                "UnconfirmedOnly": (2000, False),
                "MixedUser1": (1500, True),
                "MixedUser2": (2500, False),
            },
            "total_rewards": 7000,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        # Check that all contributors are present with correct statuses
        assert "ConfirmedOnly 1,000 ✅" in result
        assert "UnconfirmedOnly 2,000 ⍻" in result
        assert "MixedUser1 1,500 ✅" in result
        assert "MixedUser2 2,500 ⍻" in result
        assert "Cycle total: 7,000" in result

    def test_models_cycle_formatted_cycle_info_zero_reward_contributors(self):
        """Test formatted_cycle_info with zero reward contributors."""
        data = {
            "id": 10,
            "start": "2024-06-01T00:00:00",
            "end": "2024-06-30T23:59:59",
            "contributor_rewards": {
                "ZeroRewardConfirmed": (0, True),
                "ZeroRewardUnconfirmed": (0, False),
                "NormalReward": (1000, True),
            },
            "total_rewards": 1000,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        expected_lines = [
            "The current cycle #10 started on 2024-06-01 and ends on 2024-06-30",
            "",
            "**Contributors & Rewards:**",
            "",
            "ZeroRewardConfirmed 0 ✅",
            "ZeroRewardUnconfirmed 0 ⍻",
            "NormalReward 1,000 ✅",
            "",
            "Cycle total: 1,000",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_models_cycle_formatted_cycle_info_special_characters_in_names(self):
        """Test formatted_cycle_info with special characters in contributor names."""
        data = {
            "id": 11,
            "start": "2024-07-01T00:00:00",
            "end": "2024-07-31T23:59:59",
            "contributor_rewards": {
                "User-With-Dash": (1000, True),
                "User_With_Underscore": (2000, False),
                "User.With.Dots": (3000, True),
                "User With Spaces": (4000, False),
            },
            "total_rewards": 10000,
        }
        cycle = Cycle(data)
        result = cycle.formatted_cycle_info(current=True)

        # Check that all special character names are handled correctly
        assert "User-With-Dash 1,000 ✅" in result
        assert "User_With_Underscore 2,000 ⍻" in result
        assert "User.With.Dots 3,000 ✅" in result
        assert "User With Spaces 4,000 ⍻" in result
        assert "Cycle total: 10,000" in result

    def test_models_cycle_formatted_cycle_info_default_current_parameter(self):
        """Test formatted_cycle_info uses current=True by default."""
        data = {
            "id": 12,
            "start": "2024-08-01T00:00:00",
            "end": "2024-08-31T23:59:59",
            "contributor_rewards": {
                "TestUser": (1000, True),
            },
            "total_rewards": 1000,
        }
        cycle = Cycle(data)
        result_default = cycle.formatted_cycle_info()  # No parameter
        result_explicit = cycle.formatted_cycle_info(current=True)

        assert result_default == result_explicit
        assert "current cycle" in result_default
        assert "ends" in result_default
