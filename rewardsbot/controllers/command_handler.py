import logging

import discord
from discord.ui import Modal, TextInput

from services.suggestion_service import SuggestionService

logger = logging.getLogger("discord.commands")


class SuggestRewardModal(Modal, title="Suggest a Reward"):
    type_input = TextInput(
        label="Contribution type (F, B, CT...)",
        placeholder="F, B, CT, TWR, D, IC, S, AT",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=10,
    )

    level_input = TextInput(
        label="Level - time spent [1-3]",
        placeholder="1, 2, or 3",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=1,
    )

    user_input = TextInput(
        label="The contributor",
        placeholder="Username",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=32,
    )

    def __init__(self, target_message: discord.Message):
        super().__init__()
        self.target_message = target_message
        # Pre-fill the user input with the message author
        self.user_input.default = target_message.author.name

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        contribution_type = self.type_input.value.upper()
        level = self.level_input.value
        username = self.user_input.value
        message_url = self.target_message.jump_url

        try:
            # Get the bot instance to access the api_service
            bot = interaction.client
            await SuggestionService.create_suggestion(
                bot.api_service, contribution_type, level, username, message_url
            )
            await interaction.followup.send(
                f"✅ Suggestion for [{contribution_type}{level}] submitted for {username}.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Suggestion submission error: {e}")
            await interaction.followup.send(
                f"❌ Failed to submit suggestion: {str(e)}", ephemeral=True
            )
