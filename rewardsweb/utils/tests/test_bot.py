"""Testing module for :py:mod:`utils.bot` module."""

import os
from unittest import mock

import pytest

from utils.bot import add_reaction_to_message, parse_discord_url


class TestUtilsBotFunctions:
    """Testing class for :py:mod:`utils.bot` functions."""

    # # parse_discord_url
    @pytest.mark.parametrize(
        "url",
        [
            "http://discord.com/channels/906917846754418770/1028021510453084161/1353382023309562020",
            "https://github.com/asastats/channel/issues/587",
            "https://trello.com/c/mgeYvP0Z",
            "https://twitter.com/username/status/1507097109320769539",
            "https://www.reddit.com/r/asastats/comments/u0uvjp/new_staking_platform_will_you_add_it/",
            "http://discord.com/channels/1028021510453084161/1353382023309562020",
            "https://discord.com/channels/a/1020298428061847612/1022852395757211728",
            "https://discord.com/channels/906917846754418770/b/1022852395757211728",
            "https://discord.com/channels/906917846754418770/1020298428061847612/c",
            "https://discord.com/channels/906917846754418770/1020298428061847612/1022852395757211728a",
            "https://discord.com/channels/999999999999999999/1028021510453084161/1353382023309562020",
            "https://discord.com/channels/906917846754418770/1028021510453084161/",
            "https://example.com/channels/906917846754418770/1028021510453084161/1353382023309562020",
        ],
    )
    def test_utils_bot_parse_discord_url_for_wrong_pattern(self, url):
        assert not parse_discord_url(url)

    def test_utils_bot_parse_discord_url_for_wrong_server(self):
        url = "https://discord.com/channels/906917846754418771/1028021510453084161/1353382117823746178"
        assert not parse_discord_url(url)

    def test_utils_bot_parse_discord_url_for_valid_message(self):
        url = "https://discord.com/channels/906917846754418770/1028021510453084161/1353382023309562020"
        returned = parse_discord_url(url)
        assert returned == (
            "906917846754418770",
            "1028021510453084161",
            "1353382023309562020",
        )

    # # add_reaction_to_message
    def test_utils_bot_add_reaction_to_message_for_error(self):
        channel_id, message_id, emoji = (
            "123456789",
            "987654321",
            "python:123456789012345678",
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        url = (
            f"https://discord.com/api/v10/channels/{channel_id}/"
            f"messages/{message_id}/reactions/{emoji}/@me"
        )
        with mock.patch("utils.bot.requests.put") as mocked_put, mock.patch(
            "utils.bot.logger"
        ) as mocked_logger:
            mocked_put.return_value.status_code = 505
            mocked_put.return_value.text = "error text"
            returned = add_reaction_to_message(channel_id, message_id, emoji)
            assert returned is False
            mocked_put.assert_called_once_with(url, headers=headers)
            mocked_logger.error.assert_called_once_with(
                "Failed to add reaction: 505 - error text"
            )

    def test_utils_bot_add_reaction_to_message_functionality(self):
        channel_id, message_id, emoji = (
            "123456789",
            "987654321",
            "python:123456789012345678",
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        url = (
            f"https://discord.com/api/v10/channels/{channel_id}/"
            f"messages/{message_id}/reactions/{emoji}/@me"
        )
        with mock.patch("utils.bot.requests.put") as mocked_put, mock.patch(
            "utils.bot.logger"
        ) as mocked_logger:
            mocked_put.return_value.status_code = 204
            returned = add_reaction_to_message(channel_id, message_id, emoji)
            assert returned is True
            mocked_put.assert_called_once_with(url, headers=headers)
            mocked_logger.info.assert_called_once_with(
                f"Emoji {emoji} added successfully!"
            )
