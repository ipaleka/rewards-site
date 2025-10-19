"""Cycle data models and formatting utilities.

This module provides the Cycle class for handling reward cycle data
and formatting it for display in Discord messages.

:func confirmed_status: Utility function to get status emoji
:class Cycle: Main cycle data model
"""

from datetime import datetime


def confirmed_status(confirmed):
    """Get emoji status indicator for confirmation status.

    :param confirmed: Whether the reward is confirmed
    :type confirmed: bool
    :return: Checkmark emoji if confirmed, cross mark if not
    :rtype: str
    """
    return "✅" if confirmed else "⍻"


class Cycle:
    """Represents a reward cycle with contributor rewards.

    This class handles cycle data and provides methods to format
    cycle information for display in Discord messages.

    :ivar id: Unique identifier for the cycle
    :ivar start: Start date of the cycle
    :ivar end: End date of the cycle
    :ivar contributor_rewards: Dictionary of contributor rewards
    :ivar total_rewards: Total rewards for the cycle
    """

    def __init__(self, data):
        """Initialize Cycle with data dictionary.

        :param data: Dictionary containing cycle data
        :type data: dict
        :raises ValueError: If start or end dates are missing or invalid
        """
        self.id = data.get("id")

        # Handle missing dates with proper error checking
        start_date = data.get("start")
        end_date = data.get("end")

        if not start_date or not end_date:
            raise ValueError("Start and end dates are required")

        try:
            self.start = datetime.fromisoformat(start_date)
            self.end = datetime.fromisoformat(end_date)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date format: {e}")

        self.contributor_rewards = data.get("contributor_rewards", {})
        self.total_rewards = data.get("total_rewards", 0)

    def formatted_cycle_info(self, current=True):
        """Format cycle information for display in Discord.

        :param current: Whether this is the current cycle
        :type current: bool
        :return: Formatted cycle information string
        :rtype: str
        """
        # Handle empty contributor rewards gracefully
        if self.contributor_rewards:
            rewards_info = "\n".join(
                f"{name} {reward:,} {confirmed_status(confirmed)}"
                for name, (reward, confirmed) in self.contributor_rewards.items()
            )
            rewards_section = f"\n\n**Contributors & Rewards:**\n\n{rewards_info}"
        else:
            rewards_section = "\n\n**Contributors & Rewards:**\n\nNo contributors yet"

        prefix, suffix = ("current ", "s") if current else ("", "ed")
        return (
            f"The {prefix}cycle #{self.id} started on {self.start.strftime('%Y-%m-%d')} "
            f"and end{suffix} on {self.end.strftime('%Y-%m-%d')}"
            f"{rewards_section}\n\n"
            f"Cycle total: {self.total_rewards:,}"
        )
