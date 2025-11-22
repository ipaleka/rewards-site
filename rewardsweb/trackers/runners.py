"""Module containing social media trackers' run functions."""

import asyncio

from trackers.config import (
    discord_config,
    discord_guilds,
    reddit_config,
    reddit_subreddits,
    telegram_chats,
    telegram_config,
    twitter_config,
)
from trackers.discord import DiscordTracker
from trackers.parser import MessageParser
from trackers.reddit import RedditTracker
from trackers.telegram import TelegramTracker
from trackers.twitter import TwitterTracker


def run_discord_tracker():
    """Initialize related arguments and run asynchronous Discord mentions tracker.

    :var tracker: custom Discord tracker instance
    :type tracker: :class:`trackers.discord.DiscordTracker`
    """
    tracker = DiscordTracker(
        parse_message_callback=MessageParser().parse,
        discord_config=discord_config(),
        guilds_collection=discord_guilds(),
    )
    asyncio.run(tracker.run_continuous(historical_check_interval=300))


def run_reddit_tracker():
    """Initialize related arguments and run Reddit mentions tracker.

    :var tracker: custom Reddit tracker instance
    :type tracker: :class:`trackers.reddit.RedditTracker`
    """
    tracker = RedditTracker(
        parse_message_callback=MessageParser().parse,
        reddit_config=reddit_config(),
        subreddits_to_track=reddit_subreddits(),
    )
    tracker.run(poll_interval_minutes=30)


def run_telegram_tracker():
    """Initialize related arguments and run Telegram mentions tracker.

    :var tracker: custom Telegram tracker instance
    :type tracker: :class:`trackers.telegram.TelegramTracker`
    """
    tracker = TelegramTracker(
        parse_message_callback=MessageParser().parse,
        telegram_config=telegram_config(),
        chats_collection=telegram_chats(),
    )
    tracker.run(poll_interval_minutes=30)


def run_twitter_tracker():
    """Initialize related arguments and run Twitter mentions tracker.

    :var tracker: custom Twitter tracker instance
    :type tracker: :class:`trackers.twitter.TwitterTracker`
    """
    tracker = TwitterTracker(
        parse_message_callback=MessageParser().parse, twitter_config=twitter_config()
    )
    tracker.run(poll_interval_minutes=15)
