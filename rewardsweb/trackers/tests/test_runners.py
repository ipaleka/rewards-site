"""Testing module for :py:mod:`trackers.runners` module."""

import asyncio

from trackers.runners import (
    run_discord_tracker,
    run_reddit_tracker,
    run_telegram_tracker,
    run_twitter_tracker,
)


class TestTrackersRunners:
    """Testing class for :py:mod:`trackers.runners` module."""

    def test_trackers_runners_run_reddit_tracker_functionality(self, mocker):
        parser, tracker = mocker.MagicMock(), mocker.MagicMock()
        mocked_parser = mocker.patch(
            "trackers.runners.MessageParser",
            return_value=parser,
        )
        mocked_config = mocker.patch("trackers.runners.reddit_config")
        mocked_subreddits = mocker.patch("trackers.runners.reddit_subreddits")
        mocked_tracker = mocker.patch(
            "trackers.runners.RedditTracker",
            return_value=tracker,
        )
        run_reddit_tracker()
        mocked_parser.assert_called_once_with()
        mocked_config.assert_called_once_with()
        mocked_subreddits.assert_called_once_with()
        mocked_tracker.assert_called_once_with(
            parse_message_callback=parser.parse,
            reddit_config=mocked_config.return_value,
            subreddits_to_track=mocked_subreddits.return_value,
        )
        tracker.run.assert_called_once_with(poll_interval_minutes=30)

    # # run_discord_tracker
    def test_trackers_runners_run_discord_tracker_functionality(self, mocker):
        parser, tracker = mocker.MagicMock(), mocker.AsyncMock()
        mocked_parser = mocker.patch(
            "trackers.runners.MessageParser",
            return_value=parser,
        )
        mocked_config = mocker.patch("trackers.runners.discord_config")
        mocked_guilds = mocker.patch("trackers.runners.discord_guilds")
        mocked_tracker = mocker.patch(
            "trackers.runners.DiscordTracker", return_value=tracker
        )
        # Mock asyncio.run so no actual event loop runs
        mocked_asyncio_run = mocker.patch("trackers.runners.asyncio.run")
        run_discord_tracker()
        mocked_parser.assert_called_once_with()
        mocked_config.assert_called_once_with()
        mocked_guilds.assert_called_once_with()
        mocked_tracker.assert_called_once_with(
            parse_message_callback=parser.parse,
            discord_config=mocked_config.return_value,
            guilds_collection=mocked_guilds.return_value,
        )
        # Ensure run_continuous was called with correct args
        tracker.run_continuous.assert_called_once_with(historical_check_interval=300)
        # asyncio.run should receive that coroutine
        mocked_asyncio_run.assert_called_once()
        passed_coro = mocked_asyncio_run.call_args[0][0]
        # Manually reproduce the call
        manual_coro = tracker.run_continuous(historical_check_interval=300)
        assert asyncio.iscoroutine(manual_coro)

        # Ensure the passed coroutine is the SAME KIND of coroutine
        assert type(passed_coro) is type(manual_coro)

    # # run_telegram_tracker
    def test_trackers_runners_run_telegram_tracker_functionality(self, mocker):
        parser, tracker = mocker.MagicMock(), mocker.MagicMock()

        mocked_parser = mocker.patch(
            "trackers.runners.MessageParser",
            return_value=parser,
        )
        mocked_config = mocker.patch("trackers.runners.telegram_config")
        mocked_chats = mocker.patch("trackers.runners.telegram_chats")
        mocked_tracker = mocker.patch(
            "trackers.runners.TelegramTracker",
            return_value=tracker,
        )
        run_telegram_tracker()
        mocked_parser.assert_called_once_with()
        mocked_config.assert_called_once_with()
        mocked_chats.assert_called_once_with()
        mocked_tracker.assert_called_once_with(
            parse_message_callback=parser.parse,
            telegram_config=mocked_config.return_value,
            chats_collection=mocked_chats.return_value,
        )
        tracker.run.assert_called_once_with(poll_interval_minutes=30)

    # # run_twitter_tracker
    def test_trackers_runners_run_twitter_tracker_functionality(self, mocker):
        parser, tracker = mocker.MagicMock(), mocker.MagicMock()
        mocked_parser = mocker.patch(
            "trackers.runners.MessageParser",
            return_value=parser,
        )
        mocked_config = mocker.patch("trackers.runners.twitter_config")
        mocked_tracker = mocker.patch(
            "trackers.runners.TwitterTracker",
            return_value=tracker,
        )
        run_twitter_tracker()
        mocked_parser.assert_called_once_with()
        mocked_config.assert_called_once_with()
        mocked_tracker.assert_called_once_with(
            parse_message_callback=parser.parse,
            twitter_config=mocked_config.return_value,
        )
        tracker.run.assert_called_once_with(poll_interval_minutes=15)
