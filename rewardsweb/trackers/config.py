"""Module containing trackers configuration."""

from utils.helpers import get_env_variable


PLATFORM_CONTEXT_FIELDS = {
    "reddit": "subreddit",
    "twitter": "tweet_author",
    "telegram": "telegram_chat",
    "discord": "discord_channel",
}


def reddit_config():
    """Get Reddit configuration from environment variables.

    :var client_id: Reddit application client ID
    :type client_id: str
    :var client_secret: Reddit application client secret
    :type client_secret: str
    :var user_agent: User agent string for Reddit API
    :type user_agent: str
    :var username: Reddit bot username
    :type username: str
    :var password: Reddit bot password
    :type password: str
    :return: Reddit configuration dictionary
    :rtype: dict
    """
    return {
        "client_id": get_env_variable("TRACKER_REDDIT_CLIENT_ID", ""),
        "client_secret": get_env_variable("TRACKER_REDDIT_CLIENT_SECRET", ""),
        "user_agent": get_env_variable(
            "TRACKER_REDDIT_USER_AGENT", "SocialMentionTracker v1.0"
        ),
        "username": get_env_variable("TRACKER_REDDIT_USERNAME", ""),
        "password": get_env_variable("TRACKER_REDDIT_PASSWORD", ""),
    }


def twitter_config():
    """Get Twitter configuration from environment variables.

    :var bearer_token: Twitter API bearer token
    :type bearer_token: str
    :var consumer_key: Twitter API consumer key
    :type consumer_key: str
    :var consumer_secret: Twitter API consumer secret
    :type consumer_secret: str
    :var access_token: Twitter API access token
    :type access_token: str
    :var access_token_secret: Twitter API access token secret
    :type access_token_secret: str
    :return: Twitter configuration dictionary
    :rtype: dict
    """
    return {
        "bearer_token": get_env_variable("TRACKER_TWITTER_BEARER_TOKEN", ""),
        "consumer_key": get_env_variable("TRACKER_TWITTER_CONSUMER_KEY", ""),
        "consumer_secret": get_env_variable("TRACKER_TWITTER_CONSUMER_SECRET", ""),
        "access_token": get_env_variable("TRACKER_TWITTER_ACCESS_TOKEN", ""),
        "access_token_secret": get_env_variable(
            "TRACKER_TWITTER_ACCESS_TOKEN_SECRET", ""
        ),
    }


def telegram_config():
    """Get Telegram configuration from environment variables.

    :var api_id: Telegram API ID
    :type api_id: str
    :var api_hash: Telegram API hash
    :type api_hash: str
    :var session_name: name for Telegram session file
    :type session_name: str
    :var bot_username: Telegram bot username (without @)
    :type bot_username: str
    :return: Telegram configuration dictionary
    :rtype: dict
    """
    return {
        "api_id": get_env_variable("TRACKER_TELEGRAM_API_ID", ""),
        "api_hash": get_env_variable("TRACKER_TELEGRAM_API_HASH", ""),
        "session_name": get_env_variable(
            "TRACKER_TELEGRAM_SESSION_NAME", "telegram_tracker"
        ),
        "bot_username": get_env_variable("TRACKER_TELEGRAM_BOT_USERNAME", "").lower(),
    }


def reddit_subreddits():
    """Get list of subreddits to track from environment variable.

    :var subreddits_str: comma-separated list of subreddits from environment
    :type subreddits_str: str
    :return: list of subreddit names
    :rtype: list
    """
    subreddits_str = get_env_variable("TRACKER_REDDIT_SUBREDDITS", "")
    return [sub.strip() for sub in subreddits_str.split(",") if sub.strip()]


def telegram_chats():
    """Get list of Telegram chats to track from environment variable.

    :var chats_str: comma-separated list of chat usernames or IDs from environment
    :type chats_str: str
    :return: list of chat identifiers
    :rtype: list
    """
    chats_str = get_env_variable("TRACKER_TELEGRAM_CHATS", "")
    return [chat.strip() for chat in chats_str.split(",") if chat.strip()]
