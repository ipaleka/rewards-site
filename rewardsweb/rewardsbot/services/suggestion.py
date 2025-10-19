"""Suggestion service for handling reward suggestion operations.

This module provides the SuggestionService class for creating reward suggestions
and handling suggestion-related Discord commands.

:var logger: Suggestion service logger instance
:type logger: :class:`logging.Logger`
"""

import logging

import discord

from rewardsbot.utils.suggestion_parser import SuggestionParser

logger = logging.getLogger("discord.suggestions")


class SuggestionService:
    """Service class for suggestion-related operations.

    This class handles suggestion creation and Discord command interactions
    for reward suggestions.
    """

    @staticmethod
    async def create_suggestion(
        api_service, type_input, level_input, user_input, comment_input, message_url
    ):
        """Create a suggestion using the API service.

        :param api_service: API service instance for data posting
        :type api_service: :class:`APIService`
        :param type_input: Contribution type input from user
        :type type_input: str
        :param level_input: Contribution level input from user
        :type level_input: str
        :param user_input: Contributor username input from user
        :type user_input: str
        :param comment_input: Additional comment input from user
        :type comment_input: str
        :param message_url: URL of the message being suggested for
        :type message_url: str
        :return: API response from suggestion creation
        :rtype: dict
        :raises Exception: Any exception that occurs during suggestion creation
        """
        try:
            contribution_type = SuggestionParser.parse_reward_type(type_input.upper())

            result = await api_service.post_suggestion(
                contribution_type, level_input, user_input, comment_input, message_url
            )

            logger.info(f"✅ Suggestion created: {contribution_type} for {user_input}")
            return result

        except Exception as error:
            logger.error(f"❌ Suggestion Creation Error: {error}", exc_info=True)
            raise error

    @staticmethod
    async def handle_command(interaction: discord.Interaction):
        """Handle the /rewards suggest command.

        :param interaction: Discord interaction that triggered the command
        :type interaction: :class:`discord.Interaction`
        """
        await interaction.followup.send(
            "💡 Use the context menu (right-click on a message → Apps → Suggest) to suggest rewards!",
            ephemeral=True,
        )
