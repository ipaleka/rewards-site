"""Module containing class for tracking mentions on Telegram."""

import asyncio
import time
from datetime import datetime

from telethon import TelegramClient

from trackers.base import BaseMentionTracker


class TelegramTracker(BaseMentionTracker):
    """Tracker for Telegram mentions in specified groups/channels."""

    def __init__(self, parse_message_callback, telegram_config, chat_list):
        """Initialize Telegram tracker.

        :var parse_message_callback: function to call when mention is found
        :type parse_message_callback: callable
        :var telegram_config: configuration dictionary for Telegram API
        :type telegram_config: dict
        :var chat_list: list of chat usernames or IDs to monitor
        :type chat_list: list
        :var client: Telegram client instance
        :type client: :class:`telethon.TelegramClient` or None
        :var bot_username: username of the bot account
        :type bot_username: str
        :var tracked_chats: list of chats being monitored
        :type tracked_chats: list
        """
        super().__init__("telegram", parse_message_callback)

        self.client = TelegramClient(
            session=telegram_config.get("session_name", "telegram_tracker"),
            api_id=telegram_config["api_id"],
            api_hash=telegram_config["api_hash"],
        )

        self.bot_username = telegram_config.get("bot_username", "").lower()
        self.tracked_chats = chat_list

        self.logger.info(f"Telegram tracker initialized for {len(chat_list)} chats")
        self.log_action("initialized", f"Tracking {len(chat_list)} chats")

    async def _get_chat_entity(self, chat_identifier):
        """Get chat entity from identifier.

        :var chat_identifier: username or ID of the chat
        :type chat_identifier: str or int
        :var entity: Telegram chat entity
        :type entity: :class:`telethon.tl.types.Channel` or :class:`telethon.tl.types.Chat`
        :return: chat entity object
        :rtype: :class:`telethon.tl.types.Chat` or None
        """
        try:
            entity = await self.client.get_entity(chat_identifier)
            return entity

        except Exception as e:
            self.logger.error(f"Error getting chat entity for {chat_identifier}: {e}")
            return None

    def extract_mention_data(self, message):
        """Extract standardized data from Telegram message.

        :var message: Telegram message object
        :type message: :class:`telethon.tl.types.Message`
        :var data: extracted data dictionary
        :type data: dict
        :var chat: chat where message was sent
        :type chat: :class:`telethon.tl.types.Chat` or :class:`telethon.tl.types.Channel`
        :var reply_to_msg: message that this message replies to
        :type reply_to_msg: :class:`telethon.tl.types.Message` or None
        :return: standardized mention data
        :rtype: dict
        """

        # sender = await message.get_sender()   # fetch full user object

        # if sender:
        #     username = sender.username        # may be None if user has no @username
        #     display_name = sender.first_name
        #     user_id = sender.id

        #     print("ID:", user_id)
        #     print("Username:", username)
        #     print("Name:", display_name)


        chat = message.chat
        chat_title = getattr(chat, "title", "Private Chat")
        chat_username = getattr(chat, "username", f"chat_id_{chat.id}")
        url = (
            f"https://t.me/{chat_username}/{message.id}"
            if chat_username
            else f"chat_{chat.id}_msg_{message.id}"
        )
        data = {
            "suggester": message.sender_id,
            "suggestion_url": url,
            "contribution_url": url,
            "contributor": message.sender_id,
            "type": "message",
            "telegram_chat": chat_title,
            "chat_username": chat_username,
            "content_preview": message.text[:200] if message.text else "",
            "timestamp": (
                message.date.isoformat()
                if hasattr(message, "date")
                else datetime.now().isoformat()
            ),
            "item_id": f"telegram_{chat.id}_{message.id}",
        }

        # If it's a reply, get the parent message info
        if message.reply_to_msg_id:
            data["contribution_url"] = (
                f"https://t.me/{chat_username}/{message.reply_to_msg_id}"
                if chat_username
                else f"chat_{chat.id}_msg_{message.reply_to_msg_id}"
            )
            data["contributor"] = (
                message.reply_to_msg_id
            )  # Would need additional lookup for username

        # if message.reply_to_msg_id:
        #     # Fetch the message being replied to
        #     replied = await client.get_messages(message.chat_id, ids=message.reply_to_msg_id)

        #     if replied:
        #         replied_chat = replied.chat
        #         replied_chat_username = getattr(replied_chat, "username", None)

        #         if replied_chat_username:
        #             contribution_url = f"https://t.me/{replied_chat_username}/{replied.id}"
        #         else:
        #             contribution_url = f"chat_{replied_chat.id}_msg_{replied.id}"

        #         data["contribution_url"] = contribution_url
        #         data["contributor"] = replied.sender_id   # ID, not username
                
        #         # If you want the username of the *user* who wrote the original message:
        #         sender = await replied.get_sender()
        #         sender_username = sender.username if sender else None
        #         data["contributor_username"] = sender_username`


        return data

    async def _check_chat_mentions(self, chat_identifier):
        """Check for mentions in a specific chat.

        :var chat_identifier: username or ID of the chat to check
        :type chat_identifier: str or int
        :var mention_count: number of mentions found in this chat
        :type mention_count: int
        :var chat: chat entity object
        :type chat: :class:`telethon.tl.types.Chat` or None
        :var messages: recent messages from the chat
        :type messages: list of :class:`telethon.tl.types.Message`
        :var message: individual message from chat
        :type message: :class:`telethon.tl.types.Message`
        :var data: extracted mention data
        :type data: dict
        :return: number of new mentions processed in this chat
        :rtype: int
        """
        mention_count = 0
        chat = await self._get_chat_entity(chat_identifier)

        if not chat:
            return 0

        try:
            # Get recent messages (last 50)
            async for message in self.client.iter_messages(chat, limit=50):
                # Check if message mentions the bot
                if (
                    self.bot_username
                    and self.bot_username in (message.text or "").lower()
                    and not self.is_processed(f"telegram_{chat.id}_{message.id}")
                ):

                    data = self.extract_mention_data(message)
                    if self.process_mention(f"telegram_{chat.id}_{message.id}", data):
                        mention_count += 1

        except Exception as e:
            self.logger.error(f"Error checking chat {chat_identifier}: {e}")
            self.log_action(
                "chat_check_error", f"Chat: {chat_identifier}, Error: {str(e)}"
            )

        return mention_count

    async def check_mentions_async(self):
        """Asynchronously check for new mentions across all tracked chats.

        :var total_mentions: total number of new mentions found
        :type total_mentions: int
        :var chat: chat identifier from tracked chats
        :type chat: str or int
        :var chat_mentions: mentions found in current chat
        :type chat_mentions: int
        :return: total number of new mentions processed
        :rtype: int
        """
        if not self.client:
            return 0

        total_mentions = 0

        for chat in self.tracked_chats:
            chat_mentions = await self._check_chat_mentions(chat)
            total_mentions += chat_mentions
            # delay between chat checks
            await asyncio.sleep(60)

        return total_mentions

    def check_mentions(self):
        """Check for new mentions across all tracked chats.

        :var loop: asyncio event loop
        :type loop: :class:`asyncio.AbstractEventLoop`
        :var mention_count: number of new mentions found
        :type mention_count: int
        :return: number of new mentions processed
        :rtype: int
        """
        if not self.client:
            self.logger.error("Telegram client not available")
            return 0

        try:
            # Start the client and run the check
            with self.client:
                loop = asyncio.get_event_loop()
                mention_count = loop.run_until_complete(self.check_mentions_async())
                return mention_count

        except Exception as e:
            self.logger.error(f"Error in Telegram mention check: {e}")
            self.log_action("telegram_check_error", f"Error: {str(e)}")
            return 0

    def run(self, poll_interval_minutes=30, max_iterations=None):
        """Main run method for Telegram tracker.

        :var poll_interval_minutes: how often to check for mentions
        :type poll_interval_minutes: int
        :var max_iterations: maximum number of polls before stopping (None for infinite)
        :type max_iterations: int or None
        :var iteration: current iteration count
        :type iteration: int
        :var mentions_found: number of mentions found in current poll
        :type mentions_found: int
        """
        if not self.client:
            self.logger.error("Cannot start Telegram tracker - client not available")
            return

        self.logger.info(
            f"Starting Telegram tracker with {poll_interval_minutes} minute intervals"
        )
        self.log_action("started", f"Poll interval: {poll_interval_minutes} minutes")

        iteration = 0

        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1

                self.logger.info(
                    (
                        f"Telegram poll #{iteration} at "
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                )

                mentions_found = self.check_mentions()

                if mentions_found > 0:
                    self.logger.info(f"Found {mentions_found} new mentions")

                self.logger.info(
                    f"Telegram tracker sleeping for {poll_interval_minutes} minutes"
                )
                time.sleep(poll_interval_minutes * 60)

        except KeyboardInterrupt:
            self.logger.info("Telegram tracker stopped by user")
            self.log_action("stopped", "User interrupt")

        except Exception as e:
            self.logger.error(f"Telegram tracker error: {e}")
            self.log_action("error", f"Tracker error: {str(e)}")
            raise

        finally:
            self.cleanup()
