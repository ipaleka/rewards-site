"""Contribution data models and formatting utilities.

This module provides the Contribution class for handling contribution data
and formatting it for display in Discord messages.

:func _create_link: Utility function to create markdown links
:class Contribution: Main contribution data model
"""

import re


def _create_link(linktext, url):
    """Create a markdown formatted link.

    :param linktext: The text to display for the link
    :type linktext: str
    :param url: The URL to link to, or None for plain text
    :type url: str or None
    :return: Markdown formatted link or plain text
    :rtype: str
    """
    if url:
        return f"[{linktext}]({url})"

    return f"{linktext}"


class Contribution:
    """Represents a contribution with formatting capabilities.

    This class handles contribution data and provides methods to format
    the contribution information for display in Discord messages.

    :ivar id: Unique identifier for the contribution
    :ivar contributor_name: Name of the contributor
    :ivar cycle_id: ID of the reward cycle
    :ivar platform: Platform where contribution was made
    :ivar url: URL to the contribution
    :ivar type: Type of contribution (e.g., "[F] Forum Post")
    :ivar level: Level of contribution (1-3)
    :ivar percentage: Percentage of reward allocation
    :ivar reward: Reward amount
    :ivar confirmed: Whether the contribution is confirmed
    """

    def __init__(self, data):
        """Initialize Contribution with data dictionary.

        :param data: Dictionary containing contribution data
        :type data: dict
        """
        self.id = data.get("id")
        self.contributor_name = data.get("contributor_name")
        self.cycle_id = data.get("cycle_id")
        self.platform = data.get("platform")
        self.url = data.get("url")
        self.type = data.get("type")
        self.level = data.get("level")
        self.percentage = data.get("percentage")
        self.reward = data.get("reward")
        self.confirmed = data.get("confirmed")

    def formatted_contributions(self, is_user_summary=False):
        """Format contribution for display in Discord.

        :param is_user_summary: Whether this is for a user summary view
        :type is_user_summary: bool
        :return: Formatted contribution string with emoji status
        :rtype: str
        """
        # Handle None type safely
        type_text = self.type or ""
        type_short = re.search(r"\[(.*?)\]", type_text)
        type_short = type_short.group(1) if type_short else type_text

        reward = self.reward or 0

        # Handle empty contributor name
        contributor_display = self.contributor_name or ""

        linktext = (
            f"{type_short}{self.level}"
            if is_user_summary
            else f"{contributor_display} [{type_short}{self.level}]"
        )
        link = _create_link(linktext, self.url)
        status = "✅" if self.confirmed else "⍻"
        return f"{link} {reward:,} {status}"
