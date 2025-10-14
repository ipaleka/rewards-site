import logging

import discord
from discord.ui import Modal, TextInput

from services.cycle_service import CycleService
from services.suggestion_service import SuggestionService
from services.user_service import UserService

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
            await SuggestionService.create_suggestion(
                interaction, contribution_type, level, username, message_url
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


async def handle_slash_command(interaction: discord.Interaction):
    """Handle slash commands with proper response management"""
    if not interaction.command:
        return

    try:
        command_data = interaction.data
        logger.info(f"📋 Raw command data: {command_data}")

        options = command_data.get("options", [])
        logger.info(f"📋 Command options: {options}")

        if not options:
            await interaction.response.send_message(
                "❌ No parameters provided.", ephemeral=True
            )
            return

        # Extract parameters from the flat structure
        params = {}
        for option in options:
            params[option["name"]] = option["value"]

        logger.info(f"📋 Extracted parameters: {params}")

        subcommand = params.get("subcommand")
        username = params.get("username")
        detail = params.get("detail")

        logger.info(
            f"🎯 Parsed - Subcommand: {subcommand}, Username: {username}, Detail: {detail}"
        )

        # DEFER THE RESPONSE FIRST to avoid "thinking..." timeout
        await interaction.response.defer(thinking=True)
        logger.info("⏳ Response deferred successfully")

        # Handle the subcommand
        if subcommand == "cycle":
            logger.info("🔄 Routing to CycleService...")
            await CycleService.handle_command(interaction, detail)
        elif subcommand == "user":
            logger.info("🔄 Routing to UserService...")
            await UserService.handle_command(interaction, username)
        elif subcommand == "suggest":
            logger.info("🔄 Routing to SuggestionService...")
            await SuggestionService.handle_command(interaction)
        else:
            logger.warning(f"❌ Unknown subcommand: {subcommand}")
            await interaction.followup.send(
                f"❌ Unknown subcommand: {subcommand}", ephemeral=True
            )

    except Exception as error:
        logger.error(f"❌ Command Handling Error: {error}", exc_info=True)
        # Use followup since we already deferred
        try:
            await interaction.followup.send(
                "❌ Failed to execute the command.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
