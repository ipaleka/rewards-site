import logging

import discord

from utils.suggestion_parser import SuggestionParser

logger = logging.getLogger("discord.suggestions")


class SuggestionService:
    @staticmethod
    async def handle_command(interaction: discord.Interaction):
        await interaction.followup.send(
            ("💡 Use the context menu (right-click on a message "
             "→ Apps → Suggest Reward) to suggest rewards!"),
            ephemeral=True,
        )

    @staticmethod
    async def create_suggestion(
        interaction, type_input, level_input, user_input, message_url
    ):
        try:
            # Get the bot instance to access the api_service
            bot = interaction.client

            contribution_type = SuggestionParser.parse_reward_type(type_input.upper())

            result = await bot.api_service.post_suggestion(
                contribution_type, level_input, user_input, message_url
            )

            logger.info(f"Suggestion created: {contribution_type} for {user_input}")
            return result

        except Exception as error:
            logger.error(f"Suggestion Creation Error: {error}", exc_info=True)
            raise error
