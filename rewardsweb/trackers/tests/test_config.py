"""Testing module for :py:mod:`trackers.config` module."""

from trackers.config import (
    PLATFORM_CONTEXT_FIELDS,
    reddit_config,
    reddit_subreddits,
    telegram_chats,
    telegram_config,
    twitter_config,
)


class TestTrackersConfig:
    """Testing class for :py:mod:`trackers.config` module."""

    # PLATFORM_CONTEXT_FIELDS
    def test_trackers_database_platform_context_fields(self):
        expected_fields = {
            "reddit": "subreddit",
            "twitter": "tweet_author",
            "telegram": "telegram_chat",
            "discord": "discord_channel",
        }
        assert PLATFORM_CONTEXT_FIELDS == expected_fields

    # reddit_config
    def test_trackers_config_reddit_config_success(self, mocker):
        mock_getenv = mocker.patch("trackers.config.get_env_variable")
        mock_getenv.side_effect = lambda key, default=None: {
            "TRACKER_REDDIT_CLIENT_ID": "test_client",
            "TRACKER_REDDIT_CLIENT_SECRET": "test_secret",
            "TRACKER_REDDIT_USER_AGENT": "test_agent",
            "TRACKER_REDDIT_USERNAME": "test_user",
            "TRACKER_REDDIT_PASSWORD": "test_pass",
        }.get(key, default)

        result = reddit_config()

        expected_config = {
            "client_id": "test_client",
            "client_secret": "test_secret",
            "user_agent": "test_agent",
            "username": "test_user",
            "password": "test_pass",
        }
        assert result == expected_config

    def test_trackers_config_reddit_config_defaults(self):
        result = reddit_config()
        assert result["user_agent"] == "SocialMentionTracker v1.0"
        assert result["client_id"] == ""
        assert result["client_secret"] == ""

    # twitter_config
    def test_trackers_config_twitter_config_success(self, mocker):
        mock_getenv = mocker.patch("trackers.config.get_env_variable")
        mock_getenv.side_effect = lambda key, default=None: {
            "TRACKER_TWITTER_BEARER_TOKEN": "test_bearer",
            "TRACKER_TWITTER_CONSUMER_KEY": "test_consumer",
            "TRACKER_TWITTER_CONSUMER_SECRET": "test_secret",
            "TRACKER_TWITTER_ACCESS_TOKEN": "test_token",
            "TRACKER_TWITTER_ACCESS_TOKEN_SECRET": "test_token_secret",
        }.get(key, default)

        result = twitter_config()

        expected_config = {
            "bearer_token": "test_bearer",
            "consumer_key": "test_consumer",
            "consumer_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret",
        }
        assert result == expected_config

    # telegram_config
    def test_trackers_config_telegram_config_success(self, mocker):
        mock_getenv = mocker.patch("trackers.config.get_env_variable")
        mock_getenv.side_effect = lambda key, default=None: {
            "TRACKER_TELEGRAM_API_ID": "test_api_id",
            "TRACKER_TELEGRAM_API_HASH": "test_api_hash",
            "TRACKER_TELEGRAM_SESSION_NAME": "test_session",
            "TRACKER_TELEGRAM_BOT_USERNAME": "TestBot",
        }.get(key, default)

        result = telegram_config()

        expected_config = {
            "api_id": "test_api_id",
            "api_hash": "test_api_hash",
            "session_name": "test_session",
            "bot_username": "testbot",  # Should be lowercased
        }
        assert result == expected_config

    # reddit_subreddits
    def test_trackers_config_reddit_subreddits_success(self, mocker):
        mock_getenv = mocker.patch("trackers.config.get_env_variable")
        mock_getenv.return_value = "python, test, learnprogramming"

        result = reddit_subreddits()

        expected_list = ["python", "test", "learnprogramming"]
        assert result == expected_list

    def test_trackers_config_reddit_subreddits_empty(self, mocker):
        mocker.patch("trackers.config.get_env_variable", return_value="")

        result = reddit_subreddits()

        assert result == []

    # telegram_chats
    def test_trackers_config_telegram_chats_success(self, mocker):
        mock_getenv = mocker.patch("trackers.config.get_env_variable")
        mock_getenv.return_value = "group1, group2, @channel1"

        result = telegram_chats()

        expected_list = ["group1", "group2", "@channel1"]
        assert result == expected_list

    def test_trackers_config_telegram_chats_empty(self, mocker):
        mocker.patch("trackers.config.get_env_variable", return_value="")

        result = telegram_chats()

        assert result == []
