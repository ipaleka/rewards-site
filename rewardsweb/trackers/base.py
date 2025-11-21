"""Module containing base tracker class."""

import logging
import os

import requests

from trackers.database import MentionDatabaseManager
from utils.helpers import get_env_variable
from utils.importers import social_platform_prefixes


class BaseMentionTracker:
    """Base class for all social media mention trackers.

    :var BaseMentionTracker.logger: logger instance for this platform
    :type BaseMentionTracker.logger: :class:`logging.Logger`
    :var BaseMentionTracker.db: database manager instance
    :type BaseMentionTracker.db: :class:`trackers.database.MentionDatabaseManager`
    """

    def __init__(self, platform_name, parse_message_callback):
        """Initialize base tracker.

        :param platform_name: name of the social media platform
        :type platform_name: str
        :param parse_message_callback: function to call when mention is found
        :type parse_message_callback: callable
        """
        self.platform_name = platform_name
        self.parse_message_callback = parse_message_callback
        self.setup_logging()
        self.setup_database()

    # # setup
    def setup_database(self):
        """Setup database manager."""
        self.db = MentionDatabaseManager()

    def setup_logging(self):
        """Setup common logging configuration.

        :var logs_dir: logs directory name
        :type logs_dir: str
        :var log_filename: filename for the log file
        :type log_filename: str
        """
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        log_filename = os.path.join(logs_dir, f"{self.platform_name}_tracker.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(f"{self.platform_name}_tracker")

    # # processing
    def check_mentions(self):
        """Check for new mentions - to be implemented by subclasses.

        :return: number of new mentions found
        :rtype: int
        """
        raise NotImplementedError("Subclasses must implement check_mentions()")

    def is_processed(self, item_id):
        """Check if item has been processed.

        :param item_id: unique identifier for the social media item
        :type item_id: str
        :return: True if item has been processed, False otherwise
        :rtype: bool
        """
        return self.db.is_processed(item_id, self.platform_name)

    def mark_processed(self, item_id, data):
        """Mark item as processed in database.

        :param item_id: unique identifier for the social media item
        :type item_id: str
        :param data: mention data dictionary
        :type data: dict
        """
        self.db.mark_processed(item_id, self.platform_name, data)

    def process_mention(self, item_id, data):
        """Common mention processing logic.

        :param item_id: unique identifier for the social media item
        :type item_id: str
        :param data: mention data dictionary
        :type data: dict
        :var parsed_message: parsed message result
        :type parsed_message: dict
        :var contribution_data: formatted contribution data
        :type contribution_data: dict
        :return: True if mention was processed, False otherwise
        :rtype: bool
        """
        try:
            if self.is_processed(item_id):
                return False

            parsed_message = self.parse_message_callback(data)
            contribution_data = self.prepare_contribution_data(parsed_message, data)
            self.post_new_contribution(contribution_data)
            self.mark_processed(item_id, data)

            self.logger.info(
                f"Processed mention from {data.get('suggester', 'unknown')}"
            )
            self.log_action(
                "mention_processed",
                f"Item: {item_id}, Suggester: {data.get('suggester')}",
            )

            return True

        except Exception as e:
            self.logger.error(f"Error processing mention {item_id}: {e}")
            self.log_action("processing_error", f"Item: {item_id}, Error: {str(e)}")
            return False

    def log_action(self, action, details=""):
        """Log platform actions to database.

        :param action: description of the action performed
        :type action: str
        :param details: additional details about the action
        :type details: str
        """
        self.db.log_action(self.platform_name, action, details)

    def prepare_contribution_data(self, parsed_message, message_data):
        """Prepare contribution data for POST request from provided arguments.

        :param parsed_message: parsed message result
        :type parsed_message: dict
        :param message_data: original message data
        :type message_data: dict
        :var platform: social media provider name
        :type platform: str
        :var prefix: internal username prefix for the platform
        :type prefix: str
        :var username: contributor's username/handle in the platform
        :type username: str
        :return: dict
        """
        platform = self.platform_name.capitalize()
        prefix = next(
            prefix for name, prefix in social_platform_prefixes() if name == platform
        )
        username = message_data.get("contributor")

        return {
            **parsed_message,
            "username": f"{prefix}{username}",
            "url": message_data.get("contribution_url"),
            "platform": platform,
        }

    def post_new_contribution(self, contribution_data):
        """Send add contribution POST request to the Request API.

        :param contribution_data: formatted contribution data
        :type contribution_data: dict
        :var base_url: Rewards API base endpoints URL
        :type base_url: str
        :var response: requests' response instance
        :type response: :class:`requests.Response`
        :return: response data from Rewards API
        :rtype: dict
        """
        base_url = get_env_variable("REWARDS_API_BASE_URL", "http://127.0.0.1:8000/api")
        try:
            response = requests.post(
                f"{base_url}/addcontribution",
                json=contribution_data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.json()

        except requests.exceptions.ConnectionError:
            raise Exception(
                "Cannot connect to the API server. Make sure it's running on localhost."
            )

        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"API returned error: {e.response.status_code} - {e.response.text}"
            )

        except requests.exceptions.Timeout:
            raise Exception("API request timed out.")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")

    def cleanup(self):
        """Cleanup resources.

        Closes database connection if it exists.
        """
        if hasattr(self, "db"):
            self.db.cleanup()

    def run(self, **kwargs):
        """Main run method - to be implemented by subclasses.

        :var kwargs: platform-specific arguments
        :type kwargs: dict
        """
        raise NotImplementedError("Subclasses must implement run()")
