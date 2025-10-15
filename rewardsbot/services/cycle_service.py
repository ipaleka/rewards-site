import logging

from models.cycle import Cycle
from models.contribution import Contribution

logger = logging.getLogger("discord.cycle")


class CycleService:
    @staticmethod
    async def current_cycle_info(api_service):
        try:
            logger.info("🔗 Making API call to fetch_current_cycle...")
            cycle_data = await api_service.fetch_current_cycle()
            logger.info(f"✅ API response received: {len(str(cycle_data))} bytes")

            logger.info("🔄 Creating Cycle model...")
            cycle = Cycle(cycle_data)

            logger.info("🔄 Formatting cycle info...")
            result = cycle.formatted_cycle_info()
            logger.info("✅ Cycle info formatted successfully")

            return result

        except Exception as e:
            logger.error(f"❌ Error in current_cycle_info: {e}", exc_info=True)
            return "❌ Failed to fetch current cycle information."

    @staticmethod
    async def cycle_end_date(api_service):
        try:

            logger.info(
                "🔗 Making API call to fetch_current_cycle_plain for end date..."
            )
            cycle = await api_service.fetch_current_cycle_plain()
            logger.info(f"✅ API response received: {len(str(cycle))} bytes")

            result = f"The current cycle ends on: {cycle.get('end')}"
            logger.info(f"✅ End date formatted: {result}")

            return result

        except Exception as e:
            logger.error(f"❌ Error in cycle_end_date: {e}", exc_info=True)
            return "❌ Failed to fetch cycle end date."

    @staticmethod
    async def contributions_tail(api_service):
        try:
            logger.info("🔗 Making API call to fetch_contributions_tail...")
            contributions = await api_service.fetch_contributions_tail()
            size = (
                len(contributions)
                if isinstance(contributions, list)
                else "N/A"
            )
            logger.info(
                f"✅ API response received: type={type(contributions)},"
                f"length={size}"
            )

            if isinstance(contributions, list) and len(contributions) > 0:
                logger.info(f"🔄 Formatting {len(contributions)} contributions...")
                contributions = [
                    Contribution(data).formatted_contributions()
                    for data in contributions
                ]
                result = "Last 5 contributions:\n\n" + "\n".join(contributions)
                logger.info("✅ Contributions formatted successfully")
                return result

            else:
                logger.info("ℹ️ No contributions found for last cycle")
                return "No contributions found for the last cycle."

        except Exception as e:
            logger.error(f"❌ Error in contributions_tail: {e}", exc_info=True)
            return "❌ Failed to fetch last cycle contributions."
