import discord

from models.cycle import Cycle
from models.contribution import Contribution
from utils.api import ApiService


class CycleService:
    @staticmethod
    async def handle_command(interaction: discord.Interaction):
        try:
            # 2.6.4 has cleaner way to get options
            detail = interaction.data["options"][0]["options"][0]["value"]

            if detail == "current":
                info = await CycleService.get_current_cycle_info()
                await interaction.followup.send(info)
            elif detail == "end":
                end_date_info = await CycleService.get_cycle_end_date()
                await interaction.followup.send(end_date_info)
            elif detail == "last":
                cycle_last = await CycleService.get_cycle_last()
                await interaction.followup.send(cycle_last)
            else:
                await interaction.followup.send("❌ Invalid detail provided.")

        except Exception as error:
            print(f"Cycle Command Handling Error: {error}")
            await interaction.followup.send(
                "❌ Failed to process cycle command.", ephemeral=True
            )

    @staticmethod
    async def get_current_cycle_info():
        cycle_data = await ApiService.fetch_cycle_current()
        cycle = Cycle(cycle_data)
        return cycle.get_formatted_cycle_info()

    @staticmethod
    async def get_cycle_end_date():
        cycle_data = await ApiService.fetch_cycle_current()
        cycle = Cycle(cycle_data)
        return f"The current cycle ends on: {cycle.end.strftime('%Y-%m-%d')}"

    @staticmethod
    async def get_cycle_last():
        cycle_data = await ApiService.fetch_cycle_last()
        if isinstance(cycle_data, list) and len(cycle_data) > 0:
            contributions = [Contribution(data).format() for data in cycle_data]
            return f"Last 5 contributions:\n\n" + "\n".join(contributions)
        else:
            return "No contributions found for the last cycle."
