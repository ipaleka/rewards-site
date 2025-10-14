import logging

import discord

from models.cycle import Cycle
from models.contribution import Contribution

logger = logging.getLogger("discord.cycle")


class CycleService:
    @staticmethod
    async def handle_command(interaction: discord.Interaction, detail: str):
        try:
            logger.info(f"🎯 Processing cycle command with detail: {detail}")

            # Get the bot instance to access the api_service
            bot = interaction.client

            if detail == "current":
                logger.info("📊 Fetching current cycle info...")
                info = await CycleService.get_current_cycle_info(bot.api_service)
                logger.info("✅ Current cycle info fetched, sending response...")
                await interaction.followup.send(info)
            elif detail == "end":
                logger.info("📅 Fetching cycle end date...")
                end_date_info = await CycleService.get_cycle_end_date(bot.api_service)
                logger.info("✅ Cycle end date fetched, sending response...")
                await interaction.followup.send(end_date_info)
            elif detail == "last":
                logger.info("📋 Fetching last cycle contributions...")
                cycle_last = await CycleService.get_cycle_last(bot.api_service)
                logger.info("✅ Last cycle fetched, sending response...")
                await interaction.followup.send(cycle_last)
            else:
                logger.warning(f"❌ Invalid detail provided: {detail}")
                await interaction.followup.send("❌ Invalid detail provided.")

        except Exception as error:
            logger.error(f"❌ Cycle Command Handling Error: {error}", exc_info=True)
            await interaction.followup.send(
                "❌ Failed to process cycle command.", ephemeral=True
            )

    @staticmethod
    async def get_current_cycle_info(api_service):
        try:
            logger.info("🔗 Making API call to fetch_cycle_current...")
            cycle_data = await api_service.fetch_cycle_current()
            logger.info(f"✅ API response received: {len(str(cycle_data))} bytes")

            logger.info("🔄 Creating Cycle model...")
            cycle = Cycle(cycle_data)

            logger.info("🔄 Formatting cycle info...")
            result = cycle.get_formatted_cycle_info()
            logger.info("✅ Cycle info formatted successfully")

            return result

        except Exception as e:
            logger.error(f"❌ Error in get_current_cycle_info: {e}", exc_info=True)
            return "❌ Failed to fetch current cycle information."

    @staticmethod
    async def get_cycle_end_date(api_service):
        try:
            logger.info("🔗 Making API call to fetch_cycle_current for end date...")
            cycle_data = await api_service.fetch_cycle_current()
            logger.info(f"✅ API response received: {len(str(cycle_data))} bytes")

            logger.info("🔄 Creating Cycle model...")
            cycle = Cycle(cycle_data)

            result = f"The current cycle ends on: {cycle.end.strftime('%Y-%m-%d')}"
            logger.info(f"✅ End date formatted: {result}")

            return result

        except Exception as e:
            logger.error(f"❌ Error in get_cycle_end_date: {e}", exc_info=True)
            return "❌ Failed to fetch cycle end date."

    @staticmethod
    async def get_cycle_last(api_service):
        try:
            logger.info("🔗 Making API call to fetch_cycle_last...")
            cycle_data = await api_service.fetch_cycle_last()
            logger.info(
                f"✅ API response received: type={type(cycle_data)}, length={len(cycle_data) if isinstance(cycle_data, list) else 'N/A'}"
            )

            if isinstance(cycle_data, list) and len(cycle_data) > 0:
                logger.info(f"🔄 Formatting {len(cycle_data)} contributions...")
                contributions = [Contribution(data).format() for data in cycle_data]
                result = "Last 5 contributions:\n\n" + "\n".join(contributions)
                logger.info("✅ Contributions formatted successfully")
                return result
            else:
                logger.info("ℹ️ No contributions found for last cycle")
                return "No contributions found for the last cycle."

        except Exception as e:
            logger.error(f"❌ Error in get_cycle_last: {e}", exc_info=True)
            return "❌ Failed to fetch last cycle contributions."
