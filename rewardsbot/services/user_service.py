from models.contribution import Contribution
from utils.api import ApiService


class UserService:
    @staticmethod
    async def handle_command(interaction):
        try:
            username = interaction.data["options"][0]["options"][0]["value"]
            user_summary = await UserService.get_user_summary(username)
            await interaction.response.send_message(
                content=user_summary, allowed_mentions={"parse": []}
            )
        except Exception as error:
            print(f"User Command Handling Error: {error}")
            await interaction.response.send_message(
                "Failed to process user command.", ephemeral=True
            )

    @staticmethod
    async def get_user_summary(username):
        try:
            contributions = await ApiService.fetch_user_contributions(username)
            if not contributions:
                return f"No contributions for {username}."

            first_contribution_cycle = await ApiService.fetch_cycle_dates(
                contributions[0]["cycle_id"]
            )
            first_contribution_date = first_contribution_cycle.get("cycleEnd")
            if first_contribution_date:
                from datetime import datetime

                end_date = datetime.fromisoformat(
                    first_contribution_date.replace("Z", "+00:00")
                )
                first_contribution_formatted = f"{end_date.year}/{end_date.month:02d}"
            else:
                first_contribution_formatted = "Unknown"

            total_contributions = len(contributions)
            total_rewards = sum(
                float(contribution.get("reward", 0)) for contribution in contributions
            )

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
                f"Total rewards: {total_rewards:.2f} damo\n\n"
                f"Last contributions:\n\n{contributions_text}"
            )
        except Exception as error:
            print(f"User Summary Error: {error}")
            raise Exception("Failed to generate user summary.")
