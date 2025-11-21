"""Testing module for :py:mod:`trackers.base` module."""

from unittest import mock

import pytest
import requests

from trackers.base import BaseMentionTracker


class TestTrackersBaseMentionTracker:
    """Testing class for :class:`trackers.base.BaseMentionTracker` class."""

    # __init__
    def test_base_basementiontracker_init_success(self, mocker):
        mock_setup_logging = mocker.patch.object(BaseMentionTracker, "setup_logging")
        mock_setup_database = mocker.patch.object(BaseMentionTracker, "setup_database")

        def callback(data):
            pass

        instance = BaseMentionTracker("test_platform", callback)

        assert instance.platform_name == "test_platform"
        assert instance.parse_message_callback == callback
        mock_setup_logging.assert_called_once()
        mock_setup_database.assert_called_once()

    # setup_database
    def test_base_basementiontracker_setup_database_success(self, mocker):
        mock_database_manager = mocker.patch("trackers.base.MentionDatabaseManager")

        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_database_manager.reset_mock()

        instance.setup_database()

        mock_database_manager.assert_called_once()
        assert instance.db == mock_database_manager.return_value

    # setup_logging
    def test_base_basementiontracker_setup_logging_creates_directory(self, mocker):
        mock_basic_config = mocker.patch("logging.basicConfig")
        mock_get_logger = mocker.patch("logging.getLogger")
        mock_logger = mocker.MagicMock()
        mock_get_logger.return_value = mock_logger

        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_basic_config.reset_mock()
        mock_get_logger.reset_mock()
        with mock.patch(
            "os.path.exists", return_value=False
        ) as mock_exists, mock.patch("os.makedirs") as mock_makedirs:
            instance.setup_logging()
            mock_exists.assert_called_once_with("logs")
            mock_makedirs.assert_called_once_with("logs")

        mock_basic_config.assert_called_once()
        mock_get_logger.assert_called_once_with("test_platform_tracker")
        assert instance.logger == mock_logger

    def test_base_basementiontracker_setup_logging_success(self, mocker):
        mock_basic_config = mocker.patch("logging.basicConfig")
        mock_get_logger = mocker.patch("logging.getLogger")
        mock_logger = mocker.MagicMock()
        mock_get_logger.return_value = mock_logger

        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_basic_config.reset_mock()
        mock_get_logger.reset_mock()
        instance.setup_logging()

        mock_basic_config.assert_called_once()
        mock_get_logger.assert_called_once_with("test_platform_tracker")
        assert instance.logger == mock_logger

    # is_processed
    def test_base_basementiontracker_is_processed_true(self, mocker):
        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_db = mocker.MagicMock()
        mock_db.is_processed.return_value = True
        instance.db = mock_db

        result = instance.is_processed("test_item_id")

        assert result is True
        mock_db.is_processed.assert_called_once_with("test_item_id", "test_platform")

    def test_base_basementiontracker_is_processed_false(self, mocker):
        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_db = mocker.MagicMock()
        mock_db.is_processed.return_value = False
        instance.db = mock_db

        result = instance.is_processed("test_item_id")

        assert result is False

    # mark_processed
    def test_base_basementiontracker_mark_processed_success(self, mocker):
        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_db = mocker.MagicMock()
        instance.db = mock_db

        test_data = {
            "suggester": "test_user",
            "subreddit": "test_subreddit",
        }

        instance.mark_processed("test_item_id", test_data)

        mock_db.mark_processed.assert_called_once_with(
            "test_item_id", "test_platform", test_data
        )

    # process_mention
    def test_base_basementiontracker_process_mention_already_processed(self, mocker):
        mock_is_processed = mocker.patch.object(BaseMentionTracker, "is_processed")
        mock_is_processed.return_value = True
        mock_callback = mocker.MagicMock()

        instance = BaseMentionTracker("test_platform", mock_callback)

        result = instance.process_mention("test_item_id", {})

        assert result is False
        mock_callback.assert_not_called()

    def test_base_basementiontracker_process_mention_success(self, mocker):
        mock_is_processed = mocker.patch.object(BaseMentionTracker, "is_processed")
        mock_is_processed.return_value = False
        mock_prepare_contribution_data = mocker.patch.object(
            BaseMentionTracker, "prepare_contribution_data"
        )
        mock_post_new_contribution = mocker.patch.object(
            BaseMentionTracker, "post_new_contribution"
        )
        mock_mark_processed = mocker.patch.object(BaseMentionTracker, "mark_processed")
        mock_log_action = mocker.patch.object(BaseMentionTracker, "log_action")
        mock_logger = mocker.MagicMock()
        mock_callback = mocker.MagicMock(return_value={"parsed": "data"})

        instance = BaseMentionTracker("test_platform", mock_callback)
        instance.logger = mock_logger

        test_data = {"suggester": "test_user"}
        result = instance.process_mention("test_item_id", test_data)

        assert result is True
        mock_callback.assert_called_once_with(test_data)
        mock_prepare_contribution_data.assert_called_once_with(
            {"parsed": "data"}, test_data
        )
        mock_post_new_contribution.assert_called_once()
        mock_mark_processed.assert_called_once_with("test_item_id", test_data)
        mock_logger.info.assert_called_once_with("Processed mention from test_user")
        mock_log_action.assert_called_once_with(
            "mention_processed", "Item: test_item_id, Suggester: test_user"
        )

    def test_base_basementiontracker_process_mention_exception(self, mocker):
        mock_is_processed = mocker.patch.object(BaseMentionTracker, "is_processed")
        mock_is_processed.return_value = False
        mock_logger = mocker.MagicMock()
        mock_log_action = mocker.patch.object(BaseMentionTracker, "log_action")
        mock_callback = mocker.MagicMock(side_effect=Exception("Test error"))

        instance = BaseMentionTracker("test_platform", mock_callback)
        instance.logger = mock_logger

        result = instance.process_mention("test_item_id", {})

        assert result is False
        mock_logger.error.assert_called_once_with(
            "Error processing mention test_item_id: Test error"
        )
        mock_log_action.assert_called_once_with(
            "processing_error", "Item: test_item_id, Error: Test error"
        )

    # log_action
    def test_base_basementiontracker_log_action_success(self, mocker):
        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_db = mocker.MagicMock()
        instance.db = mock_db

        instance.log_action("test_action", "test_details")

        mock_db.log_action.assert_called_once_with(
            "test_platform", "test_action", "test_details"
        )

    # prepare_contribution_data
    def test_base_basementiontracker_prepare_contribution_data_success(self, mocker):
        mock_social_platform_prefixes = mocker.patch(
            "trackers.base.social_platform_prefixes"
        )
        mock_social_platform_prefixes.return_value = [("Testplatform", "TP_")]

        instance = BaseMentionTracker("testplatform", lambda x: None)

        parsed_message = {"title": "Test Title", "description": "Test Description"}
        message_data = {
            "contributor": "testuser",
            "contribution_url": "http://example.com",
        }

        result = instance.prepare_contribution_data(parsed_message, message_data)

        expected = {
            "title": "Test Title",
            "description": "Test Description",
            "username": "TP_testuser",
            "url": "http://example.com",
            "platform": "Testplatform",
        }
        assert result == expected

    def test_base_basementiontracker_prepare_contribution_data_no_contributor(
        self, mocker
    ):
        mock_social_platform_prefixes = mocker.patch(
            "trackers.base.social_platform_prefixes"
        )
        mock_social_platform_prefixes.return_value = [("Testplatform", "TP_")]

        instance = BaseMentionTracker("testplatform", lambda x: None)

        parsed_message = {"title": "Test Title", "description": "Test Description"}
        message_data = {"contribution_url": "http://example.com"}  # No contributor

        result = instance.prepare_contribution_data(parsed_message, message_data)

        expected = {
            "title": "Test Title",
            "description": "Test Description",
            "username": "TP_None",
            "url": "http://example.com",
            "platform": "Testplatform",
        }
        assert result == expected

    # post_new_contribution
    def test_base_basementiontracker_post_new_contribution_success(self, mocker):
        mock_get_env_variable = mocker.patch("trackers.base.get_env_variable")
        mock_get_env_variable.return_value = "http://test-api:8000/api"
        mock_requests_post = mocker.patch("requests.post")
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"success": True}
        mock_requests_post.return_value = mock_response

        instance = BaseMentionTracker("test_platform", lambda x: None)

        contribution_data = {"username": "test_user", "platform": "Testplatform"}
        result = instance.post_new_contribution(contribution_data)

        mock_requests_post.assert_called_once_with(
            "http://test-api:8000/api/addcontribution",
            json=contribution_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        assert result == {"success": True}

    def test_base_basementiontracker_post_new_contribution_connection_error(
        self, mocker
    ):
        mock_get_env_variable = mocker.patch("trackers.base.get_env_variable")
        mock_get_env_variable.return_value = "http://test-api:8000/api"
        mock_requests_post = mocker.patch("requests.post")
        mock_requests_post.side_effect = requests.exceptions.ConnectionError()

        instance = BaseMentionTracker("test_platform", lambda x: None)

        contribution_data = {"username": "test_user", "platform": "Testplatform"}

        with pytest.raises(
            Exception,
            match="Cannot connect to the API server. Make sure it's running on localhost.",
        ):
            instance.post_new_contribution(contribution_data)

    def test_base_basementiontracker_post_new_contribution_http_error(self, mocker):
        mock_get_env_variable = mocker.patch("trackers.base.get_env_variable")
        mock_get_env_variable.return_value = "http://test-api:8000/api"
        mock_requests_post = mocker.patch("requests.post")
        mock_response = mocker.MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests_post.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        instance = BaseMentionTracker("test_platform", lambda x: None)

        contribution_data = {"username": "test_user", "platform": "Testplatform"}

        with pytest.raises(Exception, match="API returned error: 400 - Bad Request"):
            instance.post_new_contribution(contribution_data)

    def test_base_basementiontracker_post_new_contribution_timeout(self, mocker):
        mock_get_env_variable = mocker.patch("trackers.base.get_env_variable")
        mock_get_env_variable.return_value = "http://test-api:8000/api"
        mock_requests_post = mocker.patch("requests.post")
        mock_requests_post.side_effect = requests.exceptions.Timeout()

        instance = BaseMentionTracker("test_platform", lambda x: None)

        contribution_data = {"username": "test_user", "platform": "Testplatform"}

        with pytest.raises(Exception, match="API request timed out."):
            instance.post_new_contribution(contribution_data)

    def test_base_basementiontracker_post_new_contribution_request_exception(
        self, mocker
    ):
        mock_get_env_variable = mocker.patch("trackers.base.get_env_variable")
        mock_get_env_variable.return_value = "http://test-api:8000/api"
        mock_requests_post = mocker.patch("requests.post")
        mock_requests_post.side_effect = requests.exceptions.RequestException(
            "Generic error"
        )

        instance = BaseMentionTracker("test_platform", lambda x: None)

        contribution_data = {"username": "test_user", "platform": "Testplatform"}

        with pytest.raises(Exception, match="API request failed: Generic error"):
            instance.post_new_contribution(contribution_data)

    def test_base_basementiontracker_post_new_contribution_default_base_url(
        self, mocker
    ):
        mock_get_env_variable = mocker.patch("trackers.base.get_env_variable")
        mock_get_env_variable.return_value = (
            "http://127.0.0.1:8000/api"  # Default value
        )
        mock_requests_post = mocker.patch("requests.post")
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"success": True}
        mock_requests_post.return_value = mock_response

        instance = BaseMentionTracker("test_platform", lambda x: None)

        contribution_data = {"username": "test_user", "platform": "Testplatform"}
        instance.post_new_contribution(contribution_data)

        mock_get_env_variable.assert_called_once_with(
            "REWARDS_API_BASE_URL", "http://127.0.0.1:8000/api"
        )
        mock_requests_post.assert_called_once_with(
            "http://127.0.0.1:8000/api/addcontribution",
            json=contribution_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    # check_mentions
    def test_base_basementiontracker_check_mentions_not_implemented(self, mocker):
        mocker.patch.object(BaseMentionTracker, "setup_logging")
        mocker.patch.object(BaseMentionTracker, "setup_database")
        instance = BaseMentionTracker("test_platform", lambda x: None)

        with pytest.raises(NotImplementedError):
            instance.check_mentions()

    # run
    def test_base_basementiontracker_run_not_implemented(self, mocker):
        mocker.patch.object(BaseMentionTracker, "setup_logging")
        mocker.patch.object(BaseMentionTracker, "setup_database")

        instance = BaseMentionTracker("test_platform", lambda x: None)

        with pytest.raises(NotImplementedError):
            instance.run()

    # cleanup
    def test_base_basementiontracker_cleanup_with_db(self, mocker):
        mocker.patch.object(BaseMentionTracker, "setup_logging")
        mocker.patch.object(BaseMentionTracker, "setup_database")

        instance = BaseMentionTracker("test_platform", lambda x: None)
        mock_db = mocker.MagicMock()
        instance.db = mock_db

        instance.cleanup()

        mock_db.cleanup.assert_called_once()

    def test_base_basementiontracker_cleanup_no_db(self, mocker):
        mocker.patch.object(BaseMentionTracker, "setup_logging")
        mocker.patch.object(BaseMentionTracker, "setup_database")
        instance = BaseMentionTracker("test_platform", lambda x: None)

        # Should not raise an exception
        instance.cleanup()