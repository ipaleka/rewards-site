"""Discord command handlers for the rewards bot.

This module contains Discord UI components and command handlers
for managing reward suggestions through modal interactions.

:var logger: Discord commands logger instance
:type logger: :class:`logging.Logger`
"""

import logging

import discord
from discord.ui import Modal, TextInput

from rewardsbot.services.suggestion import SuggestionService

logger = logging.getLogger("discord.commands")


class SuggestRewardModal(Modal, title="Suggest a Reward"):
    """Modal for submitting reward suggestions.

    This modal collects contribution details from users including
    type, level, username, and optional comments.

    :param target_message: The Discord message that triggered this modal
    :type target_message: :class:`discord.Message`
    :ivar type_input: Input field for contribution type
    :ivar level_input: Input field for contribution level (1-3)
    :ivar user_input: Input field for contributor username
    :ivar comment_input: Input field for additional comments
    :ivar target_message: Reference to the original message
    """

    type_input = TextInput(
        label="Contribution type (F, B, AT...)",
        placeholder="F, B, AT, CT, IC, TWR, D, ER",
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
    comment_input = TextInput(
        label="Additional info (name for the issue, ...)",
        placeholder="Comment",
        style=discord.TextStyle.short,
        required=False,
        min_length=1,
        max_length=100,
    )

    def __init__(self, target_message: discord.Message):
        """Initialize the modal with a target message.

        :param target_message: The message that triggered this modal
        :type target_message: :class:`discord.Message`
        """
        super().__init__()
        self.target_message = target_message
        # Pre-fill the user input with the message author
        self.user_input.default = target_message.author.name

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission.

        Processes the form data and creates a suggestion via SuggestionService.

        :param interaction: The Discord interaction that submitted the modal
        :type interaction: :class:`discord.Interaction`
        :raises Exception: Any exception during suggestion creation
        """
        await interaction.response.defer(thinking=True, ephemeral=True)

        contribution_type = self.type_input.value.upper()
        level = self.level_input.value
        username = self.user_input.value
        comment = self.comment_input.value
        message_url = self.target_message.jump_url

        try:
            # Get the bot instance to access the api_service
            bot = interaction.client
            await SuggestionService.create_suggestion(
                bot.api_service,
                contribution_type,
                level,
                username,
                comment,
                message_url,
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
