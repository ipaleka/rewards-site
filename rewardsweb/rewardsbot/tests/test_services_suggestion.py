"""Unit tests for :py:mod:`rewardsbot.services.suggestion` module.

This module contains tests for the SuggestionService class and its
suggestion creation and command handling functionality.
"""

import pytest
from unittest import mock

from rewardsbot.services.suggestion import SuggestionService
from rewardsbot.utils.suggestion_parser import SuggestionParser


class TestServicesSuggestion:
    """Testing class for :py:mod:`rewardsbot.services.suggestion` components."""

    # # SuggestionService.create_suggestion
    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_success(self, mocker):
        """Test create_suggestion successfully creates suggestion."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {"id": 123, "status": "created"}
        mock_api_service.post_suggestion.return_value = mock_api_response

        type_input = "F"
        level_input = "2"
        user_input = "test_user"
        comment_input = "Great contribution"
        message_url = "https://discord.com/channels/123/456/789"

        parsed_type = "Forum Post"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            result = await SuggestionService.create_suggestion(
                mock_api_service,
                type_input,
                level_input,
                user_input,
                comment_input,
                message_url,
            )

            SuggestionParser.parse_reward_type.assert_called_once_with("F")
            mock_api_service.post_suggestion.assert_called_once_with(
                parsed_type, level_input, user_input, comment_input, message_url
            )
            mock_logger.info.assert_called_once_with(
                "✅ Suggestion created: Forum Post for test_user"
            )
            assert result == mock_api_response

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_type_uppercase_conversion(
        self, mocker
    ):
        """Test create_suggestion converts type input to uppercase."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {"id": 124, "status": "created"}
        mock_api_service.post_suggestion.return_value = mock_api_response

        type_input = "b"  # lowercase input
        level_input = "1"
        user_input = "another_user"
        comment_input = ""
        message_url = "https://discord.com/channels/123/456/790"

        parsed_type = "Blog Post"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            result = await SuggestionService.create_suggestion(
                mock_api_service,
                type_input,
                level_input,
                user_input,
                comment_input,
                message_url,
            )

            # Verify type input was converted to uppercase
            SuggestionParser.parse_reward_type.assert_called_once_with("B")
            mock_api_service.post_suggestion.assert_called_once_with(
                parsed_type, level_input, user_input, comment_input, message_url
            )
            mock_logger.info.assert_called_once_with(
                "✅ Suggestion created: Blog Post for another_user"
            )
            assert result == mock_api_response

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_parser_error(self, mocker):
        """Test create_suggestion raises exception on parser error."""
        mock_api_service = mocker.AsyncMock()

        type_input = "INVALID"
        level_input = "2"
        user_input = "test_user"
        comment_input = "Comment"
        message_url = "https://discord.com/channels/123/456/789"

        parser_error = ValueError("Invalid contribution type: INVALID")

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", side_effect=parser_error
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            with pytest.raises(ValueError, match="Invalid contribution type: INVALID"):
                await SuggestionService.create_suggestion(
                    mock_api_service,
                    type_input,
                    level_input,
                    user_input,
                    comment_input,
                    message_url,
                )

            SuggestionParser.parse_reward_type.assert_called_once_with("INVALID")
            mock_api_service.post_suggestion.assert_not_called()
            mock_logger.error.assert_called_once_with(
                "❌ Suggestion Creation Error: Invalid contribution type: INVALID",
                exc_info=True,
            )

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_api_error(self, mocker):
        """Test create_suggestion raises exception on API error."""
        mock_api_service = mocker.AsyncMock()
        api_error = Exception("API connection failed")
        mock_api_service.post_suggestion.side_effect = api_error

        type_input = "F"
        level_input = "3"
        user_input = "api_test_user"
        comment_input = "API test"
        message_url = "https://discord.com/channels/123/456/791"

        parsed_type = "Forum Post"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            with pytest.raises(Exception, match="API connection failed"):
                await SuggestionService.create_suggestion(
                    mock_api_service,
                    type_input,
                    level_input,
                    user_input,
                    comment_input,
                    message_url,
                )

            SuggestionParser.parse_reward_type.assert_called_once_with("F")
            mock_api_service.post_suggestion.assert_called_once_with(
                parsed_type, level_input, user_input, comment_input, message_url
            )
            mock_logger.error.assert_called_once_with(
                "❌ Suggestion Creation Error: API connection failed", exc_info=True
            )

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_empty_comment(self, mocker):
        """Test create_suggestion handles empty comment input."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {"id": 125, "status": "created"}
        mock_api_service.post_suggestion.return_value = mock_api_response

        type_input = "AT"
        level_input = "1"
        user_input = "empty_comment_user"
        comment_input = ""  # Empty comment
        message_url = "https://discord.com/channels/123/456/792"

        parsed_type = "Article Translation"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            result = await SuggestionService.create_suggestion(
                mock_api_service,
                type_input,
                level_input,
                user_input,
                comment_input,
                message_url,
            )

            SuggestionParser.parse_reward_type.assert_called_once_with("AT")
            mock_api_service.post_suggestion.assert_called_once_with(
                parsed_type, level_input, user_input, comment_input, message_url
            )
            mock_logger.info.assert_called_once_with(
                "✅ Suggestion created: Article Translation for empty_comment_user"
            )
            assert result == mock_api_response

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_none_comment(self, mocker):
        """Test create_suggestion handles None comment input."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {"id": 126, "status": "created"}
        mock_api_service.post_suggestion.return_value = mock_api_response

        type_input = "CT"
        level_input = "2"
        user_input = "none_comment_user"
        comment_input = None  # None comment
        message_url = "https://discord.com/channels/123/456/793"

        parsed_type = "Code Translation"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            result = await SuggestionService.create_suggestion(
                mock_api_service,
                type_input,
                level_input,
                user_input,
                comment_input,
                message_url,
            )

            SuggestionParser.parse_reward_type.assert_called_once_with("CT")
            mock_api_service.post_suggestion.assert_called_once_with(
                parsed_type, level_input, user_input, comment_input, message_url
            )
            mock_logger.info.assert_called_once_with(
                "✅ Suggestion created: Code Translation for none_comment_user"
            )
            assert result == mock_api_response

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_special_characters(
        self, mocker
    ):
        """Test create_suggestion handles special characters in inputs."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {"id": 127, "status": "created"}
        mock_api_service.post_suggestion.return_value = mock_api_response

        type_input = "TWR"
        level_input = "3"
        user_input = "User-With-Dash_123"
        comment_input = "Comment with spaces, commas, and #hashtags!"
        message_url = "https://discord.com/channels/123/456/794"

        parsed_type = "Twitter Thread"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            result = await SuggestionService.create_suggestion(
                mock_api_service,
                type_input,
                level_input,
                user_input,
                comment_input,
                message_url,
            )

            SuggestionParser.parse_reward_type.assert_called_once_with("TWR")
            mock_api_service.post_suggestion.assert_called_once_with(
                parsed_type, level_input, user_input, comment_input, message_url
            )
            mock_logger.info.assert_called_once_with(
                "✅ Suggestion created: Twitter Thread for User-With-Dash_123"
            )
            assert result == mock_api_response

    # # SuggestionService.handle_command
    @pytest.mark.asyncio
    async def test_services_suggestion_handle_command_success(self, mocker):
        """Test handle_command sends correct instruction message."""
        mock_interaction = mocker.AsyncMock()
        mock_interaction.followup.send = mocker.AsyncMock()

        await SuggestionService.handle_command(mock_interaction)

        expected_message = "💡 Use the context menu (right-click on a message → Apps → Suggest) to suggest rewards!"
        mock_interaction.followup.send.assert_called_once_with(
            expected_message, ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_services_suggestion_handle_command_ephemeral_setting(self, mocker):
        """Test handle_command sends message as ephemeral."""
        mock_interaction = mocker.AsyncMock()
        mock_interaction.followup.send = mocker.AsyncMock()

        await SuggestionService.handle_command(mock_interaction)

        # Verify ephemeral=True is set
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_services_suggestion_handle_command_followup_usage(self, mocker):
        """Test handle_command uses followup.send instead of response.send."""
        mock_interaction = mocker.AsyncMock()
        mock_interaction.followup.send = mocker.AsyncMock()
        mock_interaction.response.send_message = mocker.AsyncMock()

        await SuggestionService.handle_command(mock_interaction)

        # Should use followup.send, not response.send_message
        mock_interaction.followup.send.assert_called_once()
        mock_interaction.response.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_services_suggestion_handle_command_propagates_discord_errors(
        self, mocker
    ):
        """Test handle_command propagates Discord API errors for framework handling."""
        mock_interaction = mocker.AsyncMock()
        discord_error = Exception("Discord API error")
        mock_interaction.followup.send = mocker.AsyncMock(side_effect=discord_error)

        # Discord commands should propagate exceptions so the Discord framework can handle them
        with pytest.raises(Exception, match="Discord API error"):
            await SuggestionService.handle_command(mock_interaction)

        mock_interaction.followup.send.assert_called_once()

    # # Integration-style tests
    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_complete_flow(self, mocker):
        """Test complete flow of create_suggestion with realistic data."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {
            "id": 128,
            "status": "created",
            "contribution_type": "Forum Post",
            "contributor": "complete_flow_user",
            "level": "2",
        }
        mock_api_service.post_suggestion.return_value = mock_api_response

        # Realistic input data
        type_input = "f"  # lowercase, should be uppercased
        level_input = "2"
        user_input = "complete_flow_user"
        comment_input = "This is a detailed comment about the forum post contribution."
        message_url = "https://discord.com/channels/906917846754418770/1028021510453084161/1353382023309562020"

        parsed_type = "Forum Post"

        with mock.patch.object(
            SuggestionParser, "parse_reward_type", return_value=parsed_type
        ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

            result = await SuggestionService.create_suggestion(
                mock_api_service,
                type_input,
                level_input,
                user_input,
                comment_input,
                message_url,
            )

            # Verify the complete flow
            SuggestionParser.parse_reward_type.assert_called_once_with("F")
            mock_api_service.post_suggestion.assert_called_once_with(
                "Forum Post",
                "2",
                "complete_flow_user",
                "This is a detailed comment about the forum post contribution.",
                "https://discord.com/channels/906917846754418770/1028021510453084161/1353382023309562020",
            )
            mock_logger.info.assert_called_once_with(
                "✅ Suggestion created: Forum Post for complete_flow_user"
            )
            assert result == mock_api_response
            assert result["id"] == 128
            assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_services_suggestion_create_suggestion_various_contribution_types(
        self, mocker
    ):
        """Test create_suggestion with various contribution types."""
        mock_api_service = mocker.AsyncMock()
        mock_api_response = {"id": 129, "status": "created"}
        mock_api_service.post_suggestion.return_value = mock_api_response

        test_cases = [
            ("F", "Forum Post"),
            ("B", "Blog Post"),
            ("AT", "Article Translation"),
            ("CT", "Code Translation"),
            ("IC", "Community Interaction"),
            ("TWR", "Twitter Thread"),
        ]

        for type_input, expected_parsed_type in test_cases:
            with mock.patch.object(
                SuggestionParser, "parse_reward_type", return_value=expected_parsed_type
            ), mock.patch("rewardsbot.services.suggestion.logger") as mock_logger:

                result = await SuggestionService.create_suggestion(
                    mock_api_service,
                    type_input,
                    "1",
                    "test_user",
                    "",
                    "https://example.com",
                )

                SuggestionParser.parse_reward_type.assert_called_once_with(type_input)
                mock_api_service.post_suggestion.assert_called_with(
                    expected_parsed_type, "1", "test_user", "", "https://example.com"
                )
                mock_logger.info.assert_called_with(
                    f"✅ Suggestion created: {expected_parsed_type} for test_user"
                )
                assert result == mock_api_response

            # Reset mocks for next iteration
            mock_api_service.post_suggestion.reset_mock()
            mock_logger.info.reset_mock()
