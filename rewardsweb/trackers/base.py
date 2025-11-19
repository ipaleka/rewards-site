"""Module containing base tracker class."""

import json
import logging
import os
import sqlite3
from datetime import datetime


class BaseMentionTracker:
    """Base class for all social media mention trackers."""

    def __init__(self, platform_name, callback_function):
        """Initialize base tracker.

        :var platform_name: name of the social media platform
        :type platform_name: str
        :var callback_function: function to call when mention is found
        :type callback_function: callable
        :var logger: logger instance for this platform
        :type logger: :class:`logging.Logger`
        :var conn: database connection
        :type conn: :class:`sqlite3.Connection`
        """
        self.platform_name = platform_name
        self.callback_function = callback_function
        self.setup_logging()
        self.setup_database()

    # # setup
    def setup_database(self):
        """Setup common database schema.

        :var cursor: database cursor
        :type cursor: :class:`sqlite3.Cursor`
        """
        self.conn = sqlite3.connect("fixtures/social_mentions.db")
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_mentions (
                item_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                suggester TEXT,
                subreddit TEXT,
                tweet_author TEXT,
                telegram_chat TEXT,
                raw_data TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mention_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                details TEXT
            )
        """
        )
        self.conn.commit()

    def setup_logging(self):
        """Setup common logging configuration.

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

        :var item_id: unique identifier for the social media item
        :type item_id: str
        :var cursor: database cursor
        :type cursor: :class:`sqlite3.Cursor`
        :return: True if item has been processed, False otherwise
        :rtype: bool
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_mentions WHERE item_id = ? AND platform = ?",
            (item_id, self.platform_name),
        )
        return cursor.fetchone() is not None

    def mark_processed(self, item_id, data):
        """Mark item as processed in database.

        :var item_id: unique identifier for the social media item
        :type item_id: str
        :var data: mention data dictionary
        :type data: dict
        :var cursor: database cursor
        :type cursor: :class:`sqlite3.Cursor`
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO processed_mentions 
               (item_id, platform, suggester, subreddit, tweet_author, telegram_chat, raw_data) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                item_id,
                self.platform_name,
                data.get("suggester"),
                data.get("subreddit"),
                data.get("tweet_author"),
                data.get("telegram_chat"),
                json.dumps(data),
            ),
        )
        self.conn.commit()

    def process_mention(self, item_id, data):
        """Common mention processing logic.

        :var item_id: unique identifier for the social media item
        :type item_id: str
        :var data: mention data dictionary
        :type data: dict
        :return: True if mention was processed, False otherwise
        :rtype: bool
        """
        try:
            if self.is_processed(item_id):
                return False

            # Add platform-specific metadata
            data["platform"] = self.platform_name
            data["processed_at"] = datetime.now().isoformat()

            # Call the user's callback function
            self.callback_function(data)

            # Mark as processed
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

        :var action: description of the action performed
        :type action: str
        :var details: additional details about the action
        :type details: str
        :var cursor: database cursor
        :type cursor: :class:`sqlite3.Cursor`
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO mention_logs (platform, action, details) VALUES (?, ?, ?)",
            (self.platform_name, action, details),
        )
        self.conn.commit()

    def cleanup(self):
        """Cleanup resources.

        Closes database connection if it exists.
        """
        if hasattr(self, "conn"):
            self.conn.close()

    def run(self, **kwargs):
        """Main run method - to be implemented by subclasses.

        :var kwargs: platform-specific arguments
        :type kwargs: dict
        """
        raise NotImplementedError("Subclasses must implement run()")
