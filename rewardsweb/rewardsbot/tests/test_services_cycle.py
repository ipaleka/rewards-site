"""Unit tests for :py:mod:`rewardsbot.services.cycle` module.

This module contains tests for the CycleService class and its
API interaction functionality.
"""

from unittest import mock

import pytest

from rewardsbot.models.contribution import Contribution
from rewardsbot.models.cycle import Cycle
from rewardsbot.services.cycle import CycleService


class TestServicesCycle:
    """Testing class for :py:mod:`rewardsbot.services.cycle` components."""

    # # CycleService.cycle_info
    @pytest.mark.asyncio
    async def test_services_cycle_cycle_info_success(self, mocker):
        """Test cycle_info returns formatted cycle information on success."""
        mock_api_service = mocker.AsyncMock()
        mock_cycle_data = {
            "id": 5,
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59",
            "contributor_rewards": {
                "user1": (1000, True),
                "user2": (1500, False),
            },
            "total_rewards": 2500,
        }
        mock_api_service.fetch_cycle.return_value = mock_cycle_data

        expected_result = "Formatted cycle info for cycle 5"

        with mock.patch.object(
            Cycle, "formatted_cycle_info", return_value=expected_result
        ), mock.patch("rewardsbot.services.cycle.logger") as mock_logger:

            result = await CycleService.cycle_info(mock_api_service, 5)

            mock_api_service.fetch_cycle.assert_called_once_with(5)
            mock_logger.info.assert_any_call("🔗 Making API call to fetch_cycle...")
            # Check that API response log contains the expected pattern without hardcoding byte count
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "bytes" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("🔄 Creating Cycle model...")
            mock_logger.info.assert_any_call("🔄 Formatting cycle info...")
            mock_logger.info.assert_any_call("✅ Cycle info formatted successfully")
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_services_cycle_cycle_info_api_error(self, mocker):
        """Test cycle_info returns error message on API exception."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_cycle.side_effect = Exception("API connection failed")

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.cycle_info(mock_api_service, 5)

            mock_api_service.fetch_cycle.assert_called_once_with(5)
            mock_logger.info.assert_called_once_with(
                "🔗 Making API call to fetch_cycle..."
            )
            mock_logger.error.assert_called_once_with(
                "❌ Error in cycle_info: API connection failed", exc_info=True
            )
            assert result == "❌ Failed to fetch cycle information."

    @pytest.mark.asyncio
    async def test_services_cycle_cycle_info_model_error(self, mocker):
        """Test cycle_info returns error message on model creation failure."""
        mock_api_service = mocker.AsyncMock()
        mock_cycle_data = {"invalid": "data"}
        mock_api_service.fetch_cycle.return_value = mock_cycle_data

        with mock.patch.object(
            Cycle, "__init__", side_effect=ValueError("Invalid date")
        ), mock.patch("rewardsbot.services.cycle.logger") as mock_logger:

            result = await CycleService.cycle_info(mock_api_service, 5)

            mock_api_service.fetch_cycle.assert_called_once_with(5)
            mock_logger.info.assert_any_call("🔗 Making API call to fetch_cycle...")
            # Check API response log without hardcoding byte count
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "bytes" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("🔄 Creating Cycle model...")
            mock_logger.error.assert_called_once_with(
                "❌ Error in cycle_info: Invalid date", exc_info=True
            )
            assert result == "❌ Failed to fetch cycle information."

    # # CycleService.current_cycle_info
    @pytest.mark.asyncio
    async def test_services_cycle_current_cycle_info_success(self, mocker):
        """Test current_cycle_info returns formatted current cycle information."""
        mock_api_service = mocker.AsyncMock()
        mock_cycle_data = {
            "id": 6,
            "start": "2024-02-01T00:00:00",
            "end": "2024-02-29T23:59:59",
            "contributor_rewards": {
                "user3": (2000, True),
            },
            "total_rewards": 2000,
        }
        mock_api_service.fetch_current_cycle.return_value = mock_cycle_data

        expected_result = "Formatted current cycle info"

        with mock.patch.object(
            Cycle, "formatted_cycle_info", return_value=expected_result
        ), mock.patch("rewardsbot.services.cycle.logger") as mock_logger:

            result = await CycleService.current_cycle_info(mock_api_service)

            mock_api_service.fetch_current_cycle.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_current_cycle..."
            )
            # Check API response log without hardcoding byte count
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "bytes" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("🔄 Creating Cycle model...")
            mock_logger.info.assert_any_call("🔄 Formatting cycle info...")
            mock_logger.info.assert_any_call("✅ Cycle info formatted successfully")
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_services_cycle_current_cycle_info_error(self, mocker):
        """Test current_cycle_info returns error message on exception."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_current_cycle.side_effect = Exception(
            "Current cycle unavailable"
        )

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.current_cycle_info(mock_api_service)

            mock_api_service.fetch_current_cycle.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "🔗 Making API call to fetch_current_cycle..."
            )
            mock_logger.error.assert_called_once_with(
                "❌ Error in current_cycle_info: Current cycle unavailable",
                exc_info=True,
            )
            assert result == "❌ Failed to fetch current cycle information."

    # # CycleService.cycle_end_date
    @pytest.mark.asyncio
    async def test_services_cycle_cycle_end_date_success(self, mocker):
        """Test cycle_end_date returns formatted end date on success."""
        mock_api_service = mocker.AsyncMock()
        mock_cycle_data = {
            "id": 7,
            "start": "2024-03-01T00:00:00",
            "end": "2024-03-31T23:59:59",
            "other_field": "ignored",
        }
        mock_api_service.fetch_current_cycle_plain.return_value = mock_cycle_data

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.cycle_end_date(mock_api_service)

            mock_api_service.fetch_current_cycle_plain.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_current_cycle_plain for end date..."
            )
            # Check API response log without hardcoding byte count
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "bytes" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call(
                "✅ End date formatted: The current cycle #7 ends on: 2024-03-31T23:59:59"
            )
            assert result == "The current cycle #7 ends on: 2024-03-31T23:59:59"

    @pytest.mark.asyncio
    async def test_services_cycle_cycle_end_date_missing_fields(self, mocker):
        """Test cycle_end_date handles missing id and end fields."""
        mock_api_service = mocker.AsyncMock()
        mock_cycle_data = {"other_field": "data"}  # Missing id and end
        mock_api_service.fetch_current_cycle_plain.return_value = mock_cycle_data

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.cycle_end_date(mock_api_service)

            mock_api_service.fetch_current_cycle_plain.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_current_cycle_plain for end date..."
            )
            # Check API response log without hardcoding byte count
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "bytes" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call(
                "✅ End date formatted: The current cycle #None ends on: None"
            )
            assert result == "The current cycle #None ends on: None"

    @pytest.mark.asyncio
    async def test_services_cycle_cycle_end_date_error(self, mocker):
        """Test cycle_end_date returns error message on exception."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_current_cycle_plain.side_effect = Exception(
            "End date unavailable"
        )

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.cycle_end_date(mock_api_service)

            mock_api_service.fetch_current_cycle_plain.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "🔗 Making API call to fetch_current_cycle_plain for end date..."
            )
            mock_logger.error.assert_called_once_with(
                "❌ Error in cycle_end_date: End date unavailable", exc_info=True
            )
            assert result == "❌ Failed to fetch cycle end date."

    # # CycleService.contributions_tail
    @pytest.mark.asyncio
    async def test_services_cycle_contributions_tail_success(self, mocker):
        """Test contributions_tail returns formatted contributions on success."""
        mock_api_service = mocker.AsyncMock()
        mock_contributions_data = [
            {
                "contributor_name": "user1",
                "type": "[F] Forum Post",
                "level": 2,
                "url": "https://example.com/1",
                "reward": 1000,
                "confirmed": True,
            },
            {
                "contributor_name": "user2",
                "type": "[B] Blog Post",
                "level": 1,
                "url": "https://example.com/2",
                "reward": 1500,
                "confirmed": False,
            },
        ]
        mock_api_service.fetch_contributions_tail.return_value = mock_contributions_data

        formatted_contributions = [
            "[user1 [F2]](https://example.com/1) 1,000 ✅",
            "[user2 [B1]](https://example.com/2) 1,500 ⍻",
        ]

        with mock.patch.object(Contribution, "formatted_contributions") as mock_format:
            mock_format.side_effect = formatted_contributions
            with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
                result = await CycleService.contributions_tail(mock_api_service)

                mock_api_service.fetch_contributions_tail.assert_called_once()
                mock_logger.info.assert_any_call(
                    "🔗 Making API call to fetch_contributions_tail..."
                )
                # Check API response log without hardcoding details
                api_response_calls = [
                    call
                    for call in mock_logger.info.call_args_list
                    if call[0][0].startswith("✅ API response received:")
                ]
                assert len(api_response_calls) == 1
                assert "type=" in api_response_calls[0][0][0]
                assert "length=" in api_response_calls[0][0][0]
                mock_logger.info.assert_any_call("🔄 Formatting 2 contributions...")
                mock_logger.info.assert_any_call(
                    "✅ Contributions formatted successfully"
                )

                expected_result = "Last 5 contributions:\n\n" + "\n".join(
                    formatted_contributions
                )
                assert result == expected_result

    @pytest.mark.asyncio
    async def test_services_cycle_contributions_tail_empty_list(self, mocker):
        """Test contributions_tail returns message for empty contributions list."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_contributions_tail.return_value = []

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.contributions_tail(mock_api_service)

            mock_api_service.fetch_contributions_tail.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_contributions_tail..."
            )
            # Check API response log without hardcoding details
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "type=" in api_response_calls[0][0][0]
            assert "length=0" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("ℹ️ No contributions found for last cycle")
            assert result == "No contributions found for the last cycle."

    @pytest.mark.asyncio
    async def test_services_cycle_contributions_tail_none_response(self, mocker):
        """Test contributions_tail handles None response from API."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_contributions_tail.return_value = None

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.contributions_tail(mock_api_service)

            mock_api_service.fetch_contributions_tail.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_contributions_tail..."
            )
            # Check API response log without hardcoding details
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "type=" in api_response_calls[0][0][0]
            assert "length=N/A" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("ℹ️ No contributions found for last cycle")
            assert result == "No contributions found for the last cycle."

    @pytest.mark.asyncio
    async def test_services_cycle_contributions_tail_non_list_response(self, mocker):
        """Test contributions_tail handles non-list response from API."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_contributions_tail.return_value = "invalid_data"

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.contributions_tail(mock_api_service)

            mock_api_service.fetch_contributions_tail.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_contributions_tail..."
            )
            # Check API response log without hardcoding details
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "type=" in api_response_calls[0][0][0]
            assert "length=N/A" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("ℹ️ No contributions found for last cycle")
            assert result == "No contributions found for the last cycle."

    @pytest.mark.asyncio
    async def test_services_cycle_contributions_tail_error(self, mocker):
        """Test contributions_tail returns error message on exception."""
        mock_api_service = mocker.AsyncMock()
        mock_api_service.fetch_contributions_tail.side_effect = Exception(
            "Contributions unavailable"
        )

        with mock.patch("rewardsbot.services.cycle.logger") as mock_logger:
            result = await CycleService.contributions_tail(mock_api_service)

            mock_api_service.fetch_contributions_tail.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "🔗 Making API call to fetch_contributions_tail..."
            )
            mock_logger.error.assert_called_once_with(
                "❌ Error in contributions_tail: Contributions unavailable",
                exc_info=True,
            )
            assert result == "❌ Failed to fetch last cycle contributions."

    @pytest.mark.asyncio
    async def test_services_cycle_contributions_tail_contribution_formatting_error(
        self, mocker
    ):
        """Test contributions_tail handles contribution formatting errors."""
        mock_api_service = mocker.AsyncMock()
        mock_contributions_data = [
            {
                "contributor_name": "user1",
                "type": "[F] Forum Post",
                "level": 2,
                "url": "https://example.com/1",
                "reward": 1000,
                "confirmed": True,
            }
        ]
        mock_api_service.fetch_contributions_tail.return_value = mock_contributions_data

        with mock.patch.object(
            Contribution,
            "formatted_contributions",
            side_effect=Exception("Formatting error"),
        ), mock.patch("rewardsbot.services.cycle.logger") as mock_logger:

            result = await CycleService.contributions_tail(mock_api_service)

            mock_api_service.fetch_contributions_tail.assert_called_once()
            mock_logger.info.assert_any_call(
                "🔗 Making API call to fetch_contributions_tail..."
            )
            # Check API response log without hardcoding details
            api_response_calls = [
                call
                for call in mock_logger.info.call_args_list
                if call[0][0].startswith("✅ API response received:")
            ]
            assert len(api_response_calls) == 1
            assert "type=" in api_response_calls[0][0][0]
            assert "length=1" in api_response_calls[0][0][0]
            mock_logger.info.assert_any_call("🔄 Formatting 1 contributions...")
            mock_logger.error.assert_called_once_with(
                "❌ Error in contributions_tail: Formatting error", exc_info=True
            )
            assert result == "❌ Failed to fetch last cycle contributions."
