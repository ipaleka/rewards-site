"""Testing module for :py:mod:`trackers.twitter` module."""

from datetime import datetime

import pytest

from trackers.twitter import TwitterTracker


class TestTrackersTwitter:
    """Testing class for :class:`trackers.twitter.TwitterTracker`."""

    # __init__
    def test_trackers_twittertracker_init_success(self, mocker, twitter_config):
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance - this will call the real __init__ but with mocked tweepy.Client
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_client.assert_called_once_with(
            bearer_token="test_bearer_token",
            consumer_key="test_consumer_key",
            consumer_secret="test_consumer_secret",
            access_token="test_access_token",
            access_token_secret="test_access_token_secret",
        )
        assert instance.bot_user_id == "12345"

    # extract_mention_data
    def test_trackers_twittertracker_extract_mention_data_reply(
        self, mocker, twitter_config
    ):
        # Mock tweepy.Client to prevent actual API calls
        mocker.patch("tweepy.Client")

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.author_id = "user123"
        mock_tweet.id = "tweet123"
        mock_tweet.text = "Hello @test_bot!"
        mock_tweet.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_tweet.conversation_id = "convo123"

        result = instance.extract_mention_data(mock_tweet)

        assert result["suggester"] == "user123"
        assert result["suggestion_url"] == "https://twitter.com/i/web/status/tweet123"
        assert result["contribution_url"] == "https://twitter.com/i/web/status/convo123"
        assert result["contributor"] == "convo123"
        assert result["type"] == "tweet"
        assert result["content_preview"] == "Hello @test_bot!"

    def test_trackers_twittertracker_extract_mention_data_no_reply(
        self, mocker, twitter_config
    ):
        # Mock tweepy.Client to prevent actual API calls
        mocker.patch("tweepy.Client")

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.author_id = "user123"
        mock_tweet.id = "tweet123"
        mock_tweet.text = "Hello @test_bot!"
        mock_tweet.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_tweet.conversation_id = "tweet123"  # Same as tweet ID (not a reply)

        result = instance.extract_mention_data(mock_tweet)

        assert result["contribution_url"] == ""
        assert result["contributor"] == ""

    # check_mentions
    def test_trackers_twittertracker_check_mentions_found(self, mocker, twitter_config):
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.id = "tweet123"
        mock_response = mocker.MagicMock()
        mock_response.data = [mock_tweet]
        instance.client.get_users_mentions.return_value = mock_response

        mock_process_mention = mocker.patch.object(instance, "process_mention")
        mock_process_mention.return_value = True
        mock_is_processed = mocker.patch.object(instance, "is_processed")
        mock_is_processed.return_value = False

        result = instance.check_mentions()

        assert result == 1
        instance.client.get_users_mentions.assert_called_once_with(
            "12345",
            tweet_fields=["created_at", "conversation_id", "author_id", "text"],
            expansions=["author_id"],
            max_results=20,
        )
        mock_process_mention.assert_called_once()

    def test_trackers_twittertracker_check_mentions_no_data(
        self, mocker, twitter_config
    ):
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_response = mocker.MagicMock()
        mock_response.data = None  # No mentions
        instance.client.get_users_mentions.return_value = mock_response

        result = instance.check_mentions()

        assert result == 0

    def test_trackers_twittertracker_check_mentions_exception(
        self, mocker, twitter_config
    ):
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        instance.client.get_users_mentions.side_effect = Exception("API error")
        mock_log_action = mocker.patch.object(instance, "log_action")

        # Mock the logger.error method
        mock_logger_error = mocker.patch.object(instance.logger, "error")

        result = instance.check_mentions()

        assert result == 0
        mock_logger_error.assert_called_with(
            "Error checking Twitter mentions: API error"
        )
        mock_log_action.assert_called_with("twitter_check_error", "Error: API error")

    def test_trackers_twittertracker_check_mentions_not_processed_true(
        self, mocker, twitter_config
    ):
        """Test check_mentions when tweet is not processed (is_processed returns False)."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.id = "tweet123"
        mock_response = mocker.MagicMock()
        mock_response.data = [mock_tweet]
        instance.client.get_users_mentions.return_value = mock_response

        # Mock is_processed to return False (not processed)
        mock_is_processed = mocker.patch.object(instance, "is_processed")
        mock_is_processed.return_value = False

        # Mock process_mention to return True
        mock_process_mention = mocker.patch.object(instance, "process_mention")
        mock_process_mention.return_value = True

        result = instance.check_mentions()

        # Verify tweet was processed when not already processed
        assert result == 1
        mock_is_processed.assert_called_with("tweet123")
        mock_process_mention.assert_called_once()

    def test_trackers_twittertracker_check_mentions_process_mention_true(
        self, mocker, twitter_config
    ):
        """Test check_mentions when process_mention returns True."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.id = "tweet123"
        mock_response = mocker.MagicMock()
        mock_response.data = [mock_tweet]
        instance.client.get_users_mentions.return_value = mock_response

        mock_is_processed = mocker.patch.object(instance, "is_processed")
        mock_is_processed.return_value = False

        # Mock process_mention to return True
        mock_process_mention = mocker.patch.object(instance, "process_mention")
        mock_process_mention.return_value = True  # process_mention returns True

        result = instance.check_mentions()

        # Verify mention_count was incremented when process_mention returned True
        assert result == 1
        mock_process_mention.assert_called_once()

    def test_trackers_twittertracker_run_success(self, mocker, twitter_config):
        """Test run method successful execution."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        # Mock check_mentions to return actual integer
        mock_check_mentions = mocker.patch.object(instance, "check_mentions")
        mock_check_mentions.return_value = 0  # Return actual integer, not MagicMock
        mocker.patch("time.sleep", side_effect=StopIteration)
        mock_log_action = mocker.patch.object(instance, "log_action")

        # Test run method
        try:
            instance.run(poll_interval_minutes=0.1, max_iterations=1)
        except StopIteration:
            pass

        mock_log_action.assert_any_call("started", "Poll interval: 0.1 minutes")

    def test_trackers_twittertracker_run_keyboard_interrupt(
        self, mocker, twitter_config
    ):
        """Test run method KeyboardInterrupt handling."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)
        instance.logger = mocker.MagicMock()

        # Mock check_mentions to return actual integer
        mocker.patch.object(instance, "check_mentions", return_value=0)
        mocker.patch("time.sleep", side_effect=KeyboardInterrupt)
        mock_log_action = mocker.patch.object(instance, "log_action")

        # Test KeyboardInterrupt handling
        instance.run(poll_interval_minutes=15, max_iterations=1)

        instance.logger.info.assert_called_with("Twitter tracker stopped by user")
        mock_log_action.assert_called_with("stopped", "User interrupt")

    def test_trackers_twittertracker_run_exception(self, mocker, twitter_config):
        """Test run method exception handling."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)
        instance.logger = mocker.MagicMock()

        mocker.patch.object(
            instance, "check_mentions", side_effect=Exception("Test error")
        )
        mock_log_action = mocker.patch.object(instance, "log_action")

        # Test exception handling
        with pytest.raises(Exception, match="Test error"):
            instance.run(poll_interval_minutes=15, max_iterations=1)

        instance.logger.error.assert_called_with("Twitter tracker error: Test error")
        mock_log_action.assert_called_with("error", "Tracker error: Test error")

    def test_trackers_twittertracker_check_mentions_already_processed(
        self, mocker, twitter_config
    ):
        """Test check_mentions when tweet is already processed (is_processed returns True)."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.id = "tweet123"
        mock_response = mocker.MagicMock()
        mock_response.data = [mock_tweet]
        instance.client.get_users_mentions.return_value = mock_response

        # Mock is_processed to return True (already processed)
        mock_is_processed = mocker.patch.object(instance, "is_processed")
        mock_is_processed.return_value = True

        mock_process_mention = mocker.patch.object(instance, "process_mention")

        result = instance.check_mentions()

        # Should return 0 because tweet was already processed
        assert result == 0
        mock_is_processed.assert_called_with("tweet123")
        mock_process_mention.assert_not_called()  # Should not be called when already processed

    def test_trackers_twittertracker_check_mentions_process_mention_false(
        self, mocker, twitter_config
    ):
        """Test check_mentions when process_mention returns False."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        mock_tweet = mocker.MagicMock()
        mock_tweet.id = "tweet123"
        mock_response = mocker.MagicMock()
        mock_response.data = [mock_tweet]
        instance.client.get_users_mentions.return_value = mock_response

        mock_is_processed = mocker.patch.object(instance, "is_processed")
        mock_is_processed.return_value = False

        # Mock process_mention to return False
        mock_process_mention = mocker.patch.object(instance, "process_mention")
        mock_process_mention.return_value = False  # process_mention returns False

        result = instance.check_mentions()

        # Should return 0 because process_mention returned False
        assert result == 0
        mock_process_mention.assert_called_once()  # Was called but returned False

    def test_trackers_twittertracker_run_infinite_loop(self, mocker, twitter_config):
        """Test run method with max_iterations=None (infinite loop scenario)."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        # Mock check_mentions to return 0
        mock_check_mentions = mocker.patch.object(instance, "check_mentions")
        mock_check_mentions.return_value = 0

        # Mock sleep to break after 2 iterations
        sleep_call_count = 0

        def sleep_side_effect(*args):
            nonlocal sleep_call_count
            sleep_call_count += 1
            if sleep_call_count >= 2:
                raise KeyboardInterrupt  # Break the infinite loop

        mocker.patch("time.sleep", side_effect=sleep_side_effect)
        mock_log_action = mocker.patch.object(instance, "log_action")

        # Run with max_iterations=None (infinite loop)
        try:
            instance.run(poll_interval_minutes=0.1, max_iterations=None)
        except KeyboardInterrupt:
            pass

        # Should have called check_mentions multiple times before breaking
        assert mock_check_mentions.call_count >= 2
        mock_log_action.assert_any_call("started", "Poll interval: 0.1 minutes")

    def test_trackers_twittertracker_run_mentions_found_logging(
        self, mocker, twitter_config
    ):
        """Test run method when mentions_found > 0 (logging branch)."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        # Mock check_mentions to return positive number
        mock_check_mentions = mocker.patch.object(instance, "check_mentions")
        mock_check_mentions.return_value = 5  # mentions_found > 0

        # Mock sleep to break after first iteration
        mocker.patch("time.sleep", side_effect=StopIteration)
        mock_logger_info = mocker.patch.object(instance.logger, "info")

        # Run one iteration
        try:
            instance.run(poll_interval_minutes=0.1, max_iterations=1)
        except StopIteration:
            pass

        # Verify logger.info was called for mentions_found > 0
        mock_logger_info.assert_any_call("Found 5 new mentions")

    def test_trackers_twittertracker_check_mentions_multiple_tweets_mixed_processing(
        self, mocker, twitter_config
    ):
        """Test check_mentions with multiple tweets, some processed, some not, some process_mention fails."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        # Create multiple mock tweets
        mock_tweet1 = mocker.MagicMock()
        mock_tweet1.id = "tweet1"
        mock_tweet2 = mocker.MagicMock()
        mock_tweet2.id = "tweet2"
        mock_tweet3 = mocker.MagicMock()
        mock_tweet3.id = "tweet3"

        mock_response = mocker.MagicMock()
        mock_response.data = [mock_tweet1, mock_tweet2, mock_tweet3]
        instance.client.get_users_mentions.return_value = mock_response

        # Mock is_processed to return different values for different tweets
        mock_is_processed = mocker.patch.object(instance, "is_processed")

        def is_processed_side_effect(tweet_id):
            if tweet_id == "tweet1":
                return False  # Not processed
            elif tweet_id == "tweet2":
                return True  # Already processed
            elif tweet_id == "tweet3":
                return False  # Not processed

        mock_is_processed.side_effect = is_processed_side_effect

        # Mock process_mention to return different values
        mock_process_mention = mocker.patch.object(instance, "process_mention")

        def process_mention_side_effect(tweet_id, data):
            if tweet_id == "tweet1":
                return True  # Successfully processed
            elif tweet_id == "tweet3":
                return False  # Failed to process

        mock_process_mention.side_effect = process_mention_side_effect

        result = instance.check_mentions()

        # Should return 1 (only tweet1 was successfully processed)
        # tweet2: skipped (already processed), tweet3: process_mention returned False
        assert result == 1

        # Verify is_processed was called for all tweets
        assert mock_is_processed.call_count == 3

        # Verify process_mention was only called for tweets that weren't processed
        assert mock_process_mention.call_count == 2
        mock_process_mention.assert_any_call("tweet1", mocker.ANY)
        mock_process_mention.assert_any_call("tweet3", mocker.ANY)

    def test_trackers_twittertracker_run_completes_normally_with_finally(
        self, mocker, twitter_config
    ):
        """Test run method completes normally and executes finally block."""
        # Mock tweepy.Client to prevent actual API calls
        mock_client = mocker.patch("tweepy.Client")
        mock_user = mocker.MagicMock()
        mock_user_data = mocker.MagicMock()
        mock_user_data.id = "12345"
        mock_user.data = mock_user_data
        mock_client.return_value.get_me.return_value = mock_user

        # Create instance
        instance = TwitterTracker(lambda x: None, twitter_config)

        # Mock check_mentions to return 0
        mock_check_mentions = mocker.patch.object(instance, "check_mentions")
        mock_check_mentions.return_value = 0

        # Mock cleanup to verify it's called in finally block
        mock_cleanup = mocker.patch.object(instance, "cleanup")

        # Mock sleep to just count iterations without interrupting
        sleep_call_count = 0

        def sleep_side_effect(*args):
            nonlocal sleep_call_count
            sleep_call_count += 1
            # Don't raise any exception - let the loop complete normally

        mocker.patch("time.sleep", side_effect=sleep_side_effect)

        # Run with max_iterations=3 - should complete normally after 3 iterations
        instance.run(poll_interval_minutes=0.001, max_iterations=3)

        # Verify check_mentions was called exactly 3 times
        assert mock_check_mentions.call_count == 3

        # Verify cleanup was called in finally block
        mock_cleanup.assert_called_once()

        # Verify sleep was called 3 times (after each check_mentions call)
        assert sleep_call_count == 3
