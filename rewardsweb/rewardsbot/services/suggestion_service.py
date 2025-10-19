import logging

import discord

from rewardsbot.utils.suggestion_parser import SuggestionParser

logger = logging.getLogger("discord.suggestions")


class SuggestionService:
    @staticmethod
    async def create_suggestion(
        api_service, type_input, level_input, user_input, comment_input, message_url
    ):
        """Create a suggestion using the API service"""
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
        """Handle the /rewards suggest command"""
        await interaction.followup.send(
            "💡 Use the context menu (right-click on a message → Apps → Suggest) to suggest rewards!",
            ephemeral=True,
        )
