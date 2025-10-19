"""Suggestion parser for validating and formatting contribution types.

This module provides the SuggestionParser class for parsing and validating
contribution type inputs and converting them to formatted display strings.

:class SuggestionParser: Main parser class for contribution types
"""


class SuggestionParser:
    """Parser for contribution type suggestions.

    This class handles the mapping of short contribution type codes
    to their full formatted display names.
    """

    @staticmethod
    def parse_reward_type(reward_type):
        """Parse a reward type code into its full formatted display name.

        :param reward_type: Short code for the contribution type
        :type reward_type: str
        :return: Formatted display name for the contribution type
        :rtype: str
        """
        reward_types = {
            "F": "[F] Feature Request",
            "B": "[B] Bug Report",
            "AT": "[AT] Admin Task",
            "CT": "[CT] Content Task",
            "IC": "[IC] Issue Creation",
            "TWR": "[TWR] Twitter Post",
            "D": "[D] Development",
            "ER": "[ER] Ecosystem Research",
        }
        return reward_types.get(reward_type, f"[{reward_type}] Unknown Type")
