import discord
from discord.ui import Modal, TextInput
from services.cycle_service import CycleService
from services.suggestion_service import SuggestionService
from services.user_service import UserService


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

    def __init__(self, target_message):
        super().__init__()
        self.target_message = target_message
        # Pre-fill the user input with the message author
        self.user_input.default = target_message.author.name

    async def on_submit(self, interaction) -> None:
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
            await interaction.followup.send(
                f"❌ Failed to submit suggestion: {str(e)}", ephemeral=True
            )


async def handle_slash_command(interaction):
    if not interaction.command:
        return

    try:
        command_data = interaction.data
        options = command_data.get("options", [])

        if not options:
            return

        subcommand = options[0].get("name")

        # Defer the response for better UX with API calls
        await interaction.response.defer(thinking=True)

        if subcommand == "cycle":
            await CycleService.handle_command(interaction)
        elif subcommand == "user":
            await UserService.handle_command(interaction)
        elif subcommand == "suggest":
            await SuggestionService.handle_command(interaction)

    except Exception as error:
        print(f"Command Handling Error: {error}")
        # Use followup if we already deferred
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ Failed to execute the command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to execute the command.", ephemeral=True
            )
