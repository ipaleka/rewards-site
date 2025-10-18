"""Testing module for :py:mod:`utils.bot` module."""

import os
from unittest import mock

import pytest

from utils.bot import _parse_discord_url, add_reaction_to_message, message_from_url


class TestUtilsBotFunctions:
    """Testing class for :py:mod:`utils.bot` functions."""

    # # _parse_discord_url
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
            "https://discord.com/channels/906917846754418770/1028021510453084161/",
            "https://example.com/channels/906917846754418770/1028021510453084161/1353382023309562020",
        ],
    )
    def test_utils_bot_parse_discord_url_for_wrong_pattern(self, url):
        assert _parse_discord_url(url) == (False, False)

    def test_utils_bot_parse_discord_url_for_wrong_server(self):
        url = "https://discord.com/channels/906917846754418771/1028021510453084161/1353382117823746178"
        assert _parse_discord_url(url) == (False, False)

    def test_utils_bot_parse_discord_url_for_valid_message(self):
        url = "https://discord.com/channels/906917846754418770/1028021510453084161/1353382023309562020"
        returned = _parse_discord_url(url)
        assert returned == (
            "1028021510453084161",
            "1353382023309562020",
        )

    # # add_reaction_to_message
    def test_utils_bot_add_reaction_to_message_for_wrong_url(self):
        channel_id, message_id, emoji = (
            "1028021510453084161",
            "1353382023309562020",
            "python:123456789012345678",
        )
        url = f"https://discord.com/channels/{channel_id}/{message_id}"
        with mock.patch("utils.bot.requests.put") as mocked_put, mock.patch(
            "utils.bot.logger"
        ) as mocked_logger:
            returned = add_reaction_to_message(url, emoji)
            assert returned is False
            mocked_put.assert_not_called()
            mocked_logger.assert_not_called()

    def test_utils_bot_add_reaction_to_message_for_error(self):
        channel_id, message_id, emoji = (
            "1028021510453084161",
            "1353382023309562020",
            "python:123456789012345678",
        )
        url = (
            f"https://discord.com/channels/906917846754418770/{channel_id}/{message_id}"
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        api_url = (
            f"https://discord.com/api/v10/channels/{channel_id}/"
            f"messages/{message_id}/reactions/{emoji}/@me"
        )
        with mock.patch("utils.bot.requests.put") as mocked_put, mock.patch(
            "utils.bot.logger"
        ) as mocked_logger:
            mocked_put.return_value.status_code = 505
            mocked_put.return_value.text = "error text"
            returned = add_reaction_to_message(url, emoji)
            assert returned is False
            mocked_put.assert_called_once_with(api_url, headers=headers)
            mocked_logger.error.assert_called_once_with(
                "Failed to add reaction: 505 - error text"
            )

    def test_utils_bot_add_reaction_to_message_functionality(self):
        channel_id, message_id, emoji = (
            "1028021510453084161",
            "1353382023309562020",
            "python:123456789012345678",
        )
        url = (
            f"https://discord.com/channels/906917846754418770/{channel_id}/{message_id}"
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        api_url = (
            f"https://discord.com/api/v10/channels/{channel_id}/"
            f"messages/{message_id}/reactions/{emoji}/@me"
        )
        with mock.patch("utils.bot.requests.put") as mocked_put, mock.patch(
            "utils.bot.logger"
        ) as mocked_logger:
            mocked_put.return_value.status_code = 204
            returned = add_reaction_to_message(url, emoji)
            assert returned is True
            mocked_put.assert_called_once_with(api_url, headers=headers)
            mocked_logger.info.assert_called_once_with(
                f"Emoji {emoji} added successfully!"
            )

    # # message_from_url
    def test_utils_bot_message_from_url_for_wrong_url(self):
        channel_id, message_id = "1028021510453084161", "1353382023309562020"
        url = f"https://discord.com/channels/{channel_id}/{message_id}"
        with mock.patch("utils.bot.requests.get") as mocked_get:
            returned = message_from_url(url)
            assert returned == {"success": False, "error": "Invalid URL"}
            mocked_get.assert_not_called()

    def test_utils_bot_message_from_url_for_error(self):
        channel_id, message_id = "1028021510453084161", "1353382023309562020"
        url = (
            f"https://discord.com/channels/906917846754418770/{channel_id}/{message_id}"
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        api_url = (
            f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
        )
        with mock.patch("utils.bot.requests.get") as mocked_get:
            mocked_get.return_value.status_code = 505
            mocked_get.return_value.text = "error text"
            returned = message_from_url(url)
            assert returned == {
                "success": False,
                "error": f"API Error: 505",
                "response_text": "error text",
            }
            mocked_get.assert_called_once_with(api_url, headers=headers)

    def test_utils_bot_message_from_url_for_deafult_message_data(self):
        channel_id, message_id = "1028021510453084161", "1353382023309562020"
        url = (
            f"https://discord.com/channels/906917846754418770/{channel_id}/{message_id}"
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        api_url = (
            f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
        )
        message_data = {
            "channel_id": channel_id,
            "message_id": message_id,
        }
        with mock.patch("utils.bot.requests.get") as mocked_get:
            mocked_get.return_value.status_code = 200
            mocked_get.return_value.json.return_value = message_data
            returned = message_from_url(url)
            assert returned == {
                "success": True,
                "content": "",
                "author": "Unknown",
                "timestamp": "",
                "channel_id": channel_id,
                "message_id": message_id,
                "raw_data": message_data,
            }
            mocked_get.assert_called_once_with(api_url, headers=headers)

    def test_utils_bot_message_from_url_functionality(self):
        channel_id, message_id = "1028021510453084161", "1353382023309562020"
        url = (
            f"https://discord.com/channels/906917846754418770/{channel_id}/{message_id}"
        )
        headers = {"Authorization": "Bot " + os.environ["DISCORD_BOT_TOKEN"]}
        api_url = (
            f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
        )
        message_data = {
            "content": "message content",
            "author": {"username": "Author"},
            "timestamp": "message timestamp",
            "channel_id": channel_id,
            "message_id": message_id,
        }
        with mock.patch("utils.bot.requests.get") as mocked_get:
            mocked_get.return_value.status_code = 200
            mocked_get.return_value.json.return_value = message_data
            returned = message_from_url(url)
            assert returned == {
                "success": True,
                "content": "message content",
                "author": "Author",
                "timestamp": "message timestamp",
                "channel_id": channel_id,
                "message_id": message_id,
                "raw_data": message_data,
            }
            mocked_get.assert_called_once_with(api_url, headers=headers)
