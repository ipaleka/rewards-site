"""Module containing class for tracking mentions on X/Twitter."""

import time
from datetime import datetime

import tweepy

from trackers.base import BaseMentionTracker


class TwitterTracker(BaseMentionTracker):
    """Tracker for Twitter mentions of the bot account."""

    def __init__(self, parse_message_callback, twitter_config):
        """Initialize Twitter tracker.

        :var parse_message_callback: function to call when mention is found
        :type parse_message_callback: callable
        :var twitter_config: configuration dictionary for Twitter API
        :type twitter_config: dict
        :var client: authenticated Twitter client
        :type client: :class:`tweepy.Client`
        :var bot_user: bot user information from Twitter
        :type bot_user: :class:`tweepy.models.User`
        :var bot_user_id: ID of the bot user
        :type bot_user_id: str
        """
        super().__init__("twitter", parse_message_callback)

        self.client = tweepy.Client(
            bearer_token=twitter_config["bearer_token"],
            consumer_key=twitter_config["consumer_key"],
            consumer_secret=twitter_config["consumer_secret"],
            access_token=twitter_config["access_token"],
            access_token_secret=twitter_config["access_token_secret"],
        )

        # Get bot user info
        self.bot_user = self.client.get_me()
        self.bot_user_id = self.bot_user.data.id

        self.logger.info("Twitter tracker initialized")
        self.log_action(
            "initialized", f"Tracking mentions for user ID: {self.bot_user_id}"
        )

    def extract_mention_data(self, tweet, user_map):
        """Extract standardized data from Twitter mention.

        :var tweet: Twitter tweet object
        :type tweet: :class:`tweepy.models.Tweet`
        :var data: extracted data dictionary
        :type data: dict
        :return: standardized mention data
        :rtype: dict
        """
        contributor, contribution_url = "", ""
        if tweet.referenced_tweets:
            for ref in tweet.referenced_tweets:
                if ref.type == "replied_to":
                    original_tweet = self.client.get_tweet(
                        ref.id,
                        tweet_fields=["created_at", "author_id", "text"],
                        expansions=["author_id"],
                    )
                    contribution_url = (
                        f"https://twitter.com/i/web/status/{original_tweet.id}"
                    )

                    tweet_data = original_tweet.data
                    users = original_tweet.includes["users"]
                    original_user_map = {u.id: u for u in users}
                    author = original_user_map.get(tweet_data.author_id)
                    contributor = author.username if author else ""
                    break

        suggester = user_map.get(tweet.author_id)
        suggestion_url = f"https://twitter.com/i/web/status/{tweet.id}"
        data = {
            "suggester": suggester,
            "suggestion_url": suggestion_url,
            "contribution_url": contribution_url or suggestion_url,
            "contributor": contributor or suggester,
            "type": "tweet",
            "content_preview": tweet.text[:200] if hasattr(tweet, "text") else "",
            "timestamp": (
                tweet.created_at.isoformat()
                if hasattr(tweet, "created_at")
                else datetime.now().isoformat()
            ),
            "item_id": tweet.id,
        }

        return data

    def check_mentions(self):
        """Check for new mentions on Twitter.

        :var mention_count: number of new mentions found
        :type mention_count: int
        :var mentions: recent mentions from Twitter API
        :type mentions: :class:`tweepy.models.Response`
        :var tweet: individual tweet from mentions
        :type tweet: :class:`tweepy.models.Tweet`
        :var data: extracted mention data
        :type data: dict
        :return: number of new mentions processed
        :rtype: int
        """
        mention_count = 0

        try:
            # Get recent mentions
            mentions = self.client.get_users_mentions(
                self.bot_user_id,
                tweet_fields=[
                    "created_at",
                    "conversation_id",
                    "author_id",
                    "text",
                    "referenced_tweets",
                ],
                expansions=["author_id"],
                max_results=20,
            )

            if mentions.data:
                for tweet in mentions.data:
                    if not self.is_processed(tweet.id):
                        user_map = {
                            u.id: u.username for u in mentions.includes["users"]
                        }
                        data = self.extract_mention_data(tweet, user_map)
                        if self.process_mention(tweet.id, data):
                            mention_count += 1

            self.log_action("mentions_checked", f"Found {mention_count} new mentions")

        except Exception as e:
            self.logger.error(f"Error checking Twitter mentions: {e}")
            self.log_action("twitter_check_error", f"Error: {str(e)}")

        return mention_count

    def run(self, poll_interval_minutes=15, max_iterations=None):
        """Main run method for Twitter tracker.

        :var poll_interval_minutes: how often to check for mentions
        :type poll_interval_minutes: int
        :var max_iterations: maximum number of polls before stopping (None for infinite)
        :type max_iterations: int or None
        :var iteration: current iteration count
        :type iteration: int
        :var mentions_found: number of mentions found in current poll
        :type mentions_found: int
        """
        self.logger.info(
            f"Starting Twitter tracker with {poll_interval_minutes} minute intervals"
        )
        self.log_action("started", f"Poll interval: {poll_interval_minutes} minutes")

        iteration = 0

        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1

                self.logger.info(
                    (
                        f"Twitter poll #{iteration} at "
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                )

                mentions_found = self.check_mentions()

                if mentions_found > 0:
                    self.logger.info(f"Found {mentions_found} new mentions")

                self.logger.info(
                    f"Twitter tracker sleeping for {poll_interval_minutes} minutes"
                )
                time.sleep(poll_interval_minutes * 60)

        except KeyboardInterrupt:
            self.logger.info("Twitter tracker stopped by user")
            self.log_action("stopped", "User interrupt")

        except Exception as e:
            self.logger.error(f"Twitter tracker error: {e}")
            self.log_action("error", f"Tracker error: {str(e)}")
            raise

        finally:
            self.cleanup()
