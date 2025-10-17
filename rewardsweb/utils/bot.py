"""Module containing functions related to Discord bot."""

import logging
import re

import requests

from utils.helpers import get_env_variable

logger = logging.getLogger(__name__)


def add_reaction_to_message(channel_id, message_id, emoji):
    """Add a reaction to an existing Discord message

    :param channel_id: ID of the channel containing the message
    :type channel_id: str
    :param message_id: ID of the message to react to
    :type message_id: str
    :param emoji: emoji in format name:ID
    :type emoji: str
    :var bot_token: Discord bot API access token
    :type bot_token: str
    :var headers: headers instance carrying bot token
    :type headers: dict
    :var url: fully formatted URL to add reaction to the message
    :type url: str
    :var response: HTTP response instance
    :type response: :class:`requests.Response`
    :return: Boolean
    """
    bot_token = get_env_variable("DISCORD_BOT_TOKEN")
    headers = {"Authorization": f"Bot {bot_token}"}
    url = (
        f"https://discord.com/api/v10/channels/{channel_id}/"
        f"messages/{message_id}/reactions/{emoji}/@me"
    )
    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        logger.info(f"Emoji {emoji} added successfully!")
        return True

    else:
        logger.error(
            f"Failed to add reaction: {response.status_code} - {response.text}"
        )
        return False


def parse_discord_url(url):
    """Return Discord server, channel, and message IDs parsed from provided `url`.

    :param url: URL of the Discord message to validate
    :type url: str

    :var pattern: Discord URL regex pattern
    :type pattern: str
    :var match: regex match instance
    :type match: :class:`re.Match`
    :var channel_id: ID of the channel containing the message
    :type channel_id: str
    :var subchannel_id: subchannel (server/guild channel) ID containing the message
    :type subchannel_id: str
    :var message_id: ID of the message to react to
    :type message_id: str
    :return: tuple
    """
    pattern = r"^https://discord\.com/channels/(\d+)/(\d+)/(\d+)$"
    match = re.match(pattern, url)
    if not match:
        return False

    channel_id, subchannel_id, message_id = match.groups()
    if channel_id not in get_env_variable("DISCORD_GUILD_IDS").split(","):
        return False

    return channel_id, subchannel_id, message_id
