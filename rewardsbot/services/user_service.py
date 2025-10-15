import logging


import discord

from models.contribution import Contribution

logger = logging.getLogger("discord.user")


class UserService:
    @staticmethod
    async def handle_command(interaction: discord.Interaction, username: str):
        try:
            logger.info(f"🎯 Processing user command for: {username}")

            # Get the bot instance to access the api_service
            bot = interaction.client
            user_summary = await UserService.user_summary(bot.api_service, username)

            await interaction.followup.send(
                content=user_summary, allowed_mentions={"parse": []}
            )

        except Exception as error:
            logger.error(f"❌ User Command Handling Error: {error}", exc_info=True)
            await interaction.followup.send(
                "❌ Failed to process user command.", ephemeral=True
            )

    @staticmethod
    async def user_summary(api_service, username):
        try:
            contributions = await api_service.fetch_user_contributions(username)
            if not contributions:
                return f"No contributions for {username}."

            # Get first contribution cycle dates
            first_contribution_cycle = await api_service.fetch_cycle_by_id(
                contributions[0]["cycle"]
            )
            first_contribution_date = first_contribution_cycle.get("end")

            if first_contribution_date:
                from datetime import datetime

                end_date = datetime.fromisoformat(
                    first_contribution_date.replace("Z", "+00:00")
                )
                first_contribution_formatted = f"{end_date.year}/{end_date.month:02d}"
            else:
                first_contribution_formatted = "Unknown"

            total_contributions = len(contributions)

            last_five_contributions = sorted(
                contributions, key=lambda x: x.get("id", 0), reverse=True
            )[:5]

            contributions_text = "\n".join(
                Contribution(contribution).format(True)
                for contribution in last_five_contributions
            )

            return (
                f"**{username}**\n\n"
                f"First contribution cycle: {first_contribution_formatted}\n"
                f"Total contributions: {total_contributions}\n"
                f"Last contributions:\n\n{contributions_text}"
            )

        except Exception as error:
            logger.error(f"❌ User Summary Error: {error}", exc_info=True)
            return f"❌ Failed to generate user summary for {username}."
