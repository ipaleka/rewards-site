import discord

from utils.api import ApiService
from utils.suggestion_parser import SuggestionParser


class SuggestionService:
    @staticmethod
    async def create_suggestion(
        interaction: discord.Interaction,
        type_input: str,
        level_input: str,
        user_input: str,
        message_url: str,
    ):
        try:
            contribution_type = SuggestionParser.parse_reward_type(type_input.upper())

            # 2.6.4 has better API error handling
            result = await ApiService.post_suggestion(
                contribution_type, level_input, user_input, message_url
            )

            print(f"✅ Suggestion created: {contribution_type} for {user_input}")
            return result

        except Exception as error:
            print(f"❌ Suggestion Creation Error: {error}")
            raise error  # Re-raise to be handled by modal

    @staticmethod
    async def handle_command(interaction: discord.Interaction):
        await interaction.followup.send(
            "💡 Use the context menu (right-click on a message → Apps → Suggest Reward) to suggest rewards!",
            ephemeral=True,
        )
