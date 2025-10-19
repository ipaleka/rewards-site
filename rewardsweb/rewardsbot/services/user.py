"""User service for handling user-related operations.

This module provides the UserService class for fetching and formatting
user contribution summaries and statistics.

:var logger: User service logger instance
:type logger: :class:`logging.Logger`
"""

import logging
from datetime import datetime

from rewardsbot.models.contribution import Contribution

logger = logging.getLogger("discord.user")


class UserService:
    """Service class for user-related operations.

    This class handles user contribution data fetching and formatting
    user summaries for display in Discord messages.
    """

    @staticmethod
    async def user_summary(api_service, username):
        """Generate a summary of user contributions and statistics.

        :param api_service: API service instance for data fetching
        :type api_service: :class:`APIService`
        :param username: Username to generate summary for
        :type username: str
        :return: Formatted user summary or error message
        :rtype: str
        """
        try:
            contributions = await api_service.fetch_user_contributions(username)
            if not contributions:
                return f"No contributions for {username}."

            # Get first contribution cycle dates
            first_contribution_cycle = await api_service.fetch_cycle_by_id_plain(
                contributions[0]["cycle_id"]
            )
            first_contribution_date = first_contribution_cycle.get("end")

            if first_contribution_date:
                end_date = datetime.fromisoformat(
                    first_contribution_date.replace("Z", "+00:00")
                )
                first_contribution_formatted = f"{end_date.year}/{end_date.month:02d}"

            else:
                first_contribution_formatted = "Unknown"

            total_contributions = len(contributions)
            total_rewards = sum(
                contribution.get("reward", 0) for contribution in contributions
            )

            last_five_contributions = sorted(
                contributions, key=lambda x: x.get("id", 0), reverse=True
            )[:5]

            contributions_text = "\n".join(
                Contribution(contribution).formatted_contributions(True)
                for contribution in last_five_contributions
            )

            return (
                f"**{username}**\n\n"
                f"First contribution cycle: {first_contribution_formatted}\n"
                f"Total contributions: {total_contributions}\n"
                f"Total rewards: {total_rewards:,}\n\n"
                f"Last contributions:\n\n{contributions_text}"
            )

        except Exception as error:
            logger.error(f"❌ User Summary Error: {error}", exc_info=True)
            return f"❌ Failed to generate user summary for {username}."
