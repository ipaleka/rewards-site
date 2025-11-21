"""Module containing class for tracking mentions on Discord across multiple servers."""

import asyncio
from datetime import datetime, timedelta

from discord import Client, Intents, HTTPException, Forbidden

from trackers.base import BaseMentionTracker


class MultiGuildDiscordTracker(BaseMentionTracker):
    """Discord tracker for multiple servers/guilds with automatic channel discovery.

    :param MultiGuildDiscordTracker.client: Discord client instance
    :type MultiGuildDiscordTracker.client: :class:`discord.Client` or None
    :param MultiGuildDiscordTracker.bot_user_id: user ID of the bot account
    :type MultiGuildDiscordTracker.bot_user_id: int
    :param MultiGuildDiscordTracker.tracked_guilds: list of guild IDs to monitor
    :type MultiGuildDiscordTracker.tracked_guilds: list
    :param MultiGuildDiscordTracker.auto_discover_channels: whether to auto-discover channels
    :type MultiGuildDiscordTracker.auto_discover_channels: bool
    :param MultiGuildDiscordTracker.excluded_channel_types: channel types to exclude
    :type MultiGuildDiscordTracker.excluded_channel_types: list
    """

    def __init__(self, parse_message_callback, discord_config, guild_list=None):
        """Initialize multi-guild Discord tracker.

        :param parse_message_callback: function to call when mention is found
        :type parse_message_callback: callable
        :param discord_config: configuration dictionary for Discord API
        :type discord_config: dict
        :param guild_list: list of guild IDs to monitor
        :type guild_list: list
        """
        super().__init__("discord", parse_message_callback)

        # Configure Discord intents to read messages and access guild information
        intents = Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        self.client = Client(intents=intents)
        self.bot_user_id = discord_config["bot_user_id"]
        self.tracked_guilds = guild_list or []  # Empty list means all guilds
        self.auto_discover_channels = discord_config.get("auto_discover_channels", True)

        # Channel management
        self.excluded_channel_types = discord_config.get("excluded_channel_types", [])
        self.manually_excluded_channels = discord_config.get("excluded_channels", [])
        self.manually_included_channels = discord_config.get("included_channels", [])

        # Rate limiting and state management
        self.processed_messages = set()
        self.last_channel_check = {}
        self.guild_channels = {}  # guild_id -> list of channel_ids
        self.all_tracked_channels = set()

        # Configuration
        self.rate_limit_delay = 1.0
        self.max_messages_per_channel = 20
        self.concurrent_channel_checks = 3
        self.channel_discovery_interval = 300  # 5 minutes

        self.logger.info(
            f"Multi-guild Discord tracker initialized for {len(guild_list) if guild_list else 'all'} guilds"
        )
        self.log_action(
            "initialized", f"Tracking {len(guild_list) if guild_list else 'all'} guilds"
        )

        # Set up event handlers
        self._setup_events()

    def _setup_events(self):
        """Set up Discord event handlers."""

        @self.client.event
        async def on_ready():
            """Called when the bot is logged in and ready."""
            self.logger.info(f"Discord bot logged in as {self.client.user}")
            self.logger.info(f"Connected to {len(self.client.guilds)} guilds")

            # Discover channels for all guilds
            await self._discover_all_guild_channels()

            self.log_action(
                "connected",
                f"Logged in as {self.client.user}, tracking {len(self.all_tracked_channels)} channels across {len(self.guild_channels)} guilds",
            )

        @self.client.event
        async def on_message(message):
            """Called when a message is sent in any channel the bot can see."""
            await self._handle_new_message(message)

        @self.client.event
        async def on_guild_join(guild):
            """Called when the bot joins a new guild."""
            self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
            await self._discover_guild_channels(guild)
            self.log_action("guild_joined", f"Guild: {guild.name}")

        @self.client.event
        async def on_guild_remove(guild):
            """Called when the bot is removed from a guild."""
            self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
            if guild.id in self.guild_channels:
                del self.guild_channels[guild.id]
                self._update_all_tracked_channels()
            self.log_action("guild_left", f"Guild: {guild.name}")

    async def _discover_all_guild_channels(self):
        """Discover all channels across all tracked guilds.

        :var guilds_to_process: list of guilds to process for channel discovery
        :type guilds_to_process: list of :class:`discord.Guild`
        :var guild: individual guild being processed
        :type guild: :class:`discord.Guild`
        """
        guilds_to_process = []

        if self.tracked_guilds:
            # Only process specified guilds
            for guild_id in self.tracked_guilds:
                guild = self.client.get_guild(guild_id)
                if guild:
                    guilds_to_process.append(guild)
                else:
                    self.logger.warning(f"Guild {guild_id} not found")
        else:
            # Process all guilds the bot is in
            guilds_to_process = self.client.guilds

        for guild in guilds_to_process:
            await self._discover_guild_channels(guild)

    async def _discover_guild_channels(self, guild):
        """Discover all trackable channels in a guild.

        :param guild: Discord guild to discover channels in
        :type guild: :class:`discord.Guild`
        :var channels: list of all channels in the guild
        :type channels: list of :class:`discord.abc.GuildChannel`
        :var trackable_channels: filtered list of channels to track
        :type trackable_channels: list of :class:`discord.TextChannel`
        :var channel: individual channel being processed
        :type channel: :class:`discord.abc.GuildChannel`
        :var channel_ids: list of channel IDs for this guild
        :type channel_ids: list of int
        """
        try:
            channels = await guild.fetch_channels()
            trackable_channels = []

            for channel in channels:
                # Check if channel is trackable
                if self._is_channel_trackable(channel, guild.id):
                    trackable_channels.append(channel)

            # Store channel IDs for this guild
            channel_ids = [channel.id for channel in trackable_channels]
            self.guild_channels[guild.id] = channel_ids
            self._update_all_tracked_channels()

            self.logger.info(
                f"Discovered {len(channel_ids)} trackable channels in guild '{guild.name}'"
            )

        except Exception as e:
            self.logger.error(f"Error discovering channels for guild {guild.name}: {e}")

    def _is_channel_trackable(self, channel, guild_id):
        """Check if a channel should be tracked.

        :param channel: Discord channel to check
        :type channel: :class:`discord.abc.GuildChannel`
        :param guild_id: ID of the guild containing the channel
        :type guild_id: int
        :var channel_type: type of the channel as string
        :type channel_type: str
        :var has_permission: whether bot has permission to read messages
        :type has_permission: bool
        :return: whether channel is trackable
        :rtype: bool
        """
        # Check channel type
        channel_type = str(channel.type)
        if channel_type in self.excluded_channel_types:
            return False

        # Check manual exclusions
        if channel.id in self.manually_excluded_channels:
            return False

        # Check manual inclusions (override other checks)
        if (
            self.manually_included_channels
            and channel.id in self.manually_included_channels
        ):
            return True

        # Check permissions (for text channels)
        if hasattr(channel, "permissions_for"):
            try:
                bot_member = channel.guild.get_member(self.client.user.id)
                if bot_member:
                    permissions = channel.permissions_for(bot_member)
                    has_permission = (
                        permissions.read_messages and permissions.read_message_history
                    )
                    if not has_permission:
                        return False
            except Exception:
                return False

        return True

    def _update_all_tracked_channels(self):
        """Update the set of all tracked channels across all guilds.

        :var all_channels: set of all channel IDs from all guilds
        :type all_channels: set of int
        """
        all_channels = set()
        for channel_list in self.guild_channels.values():
            all_channels.update(channel_list)
        self.all_tracked_channels = all_channels
        self.logger.debug(
            f"Updated tracked channels: {len(all_channels)} total channels"
        )

    async def _handle_new_message(self, message):
        """Handle incoming Discord messages across all tracked guilds.

        :param message: Discord message object
        :type message: :class:`discord.Message`
        :var is_tracked_guild: whether message is from a tracked guild
        :type is_tracked_guild: bool
        :var is_tracked_channel: whether message is from a tracked channel
        :type is_tracked_channel: bool
        :var is_bot_mentioned: whether the bot is mentioned in the message
        :type is_bot_mentioned: bool
        :var message_id: unique identifier for the message
        :type message_id: str
        :var data: extracted mention data
        :type data: dict
        """
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if message is from a tracked guild
        if not message.guild:
            return  # Skip DMs

        is_tracked_guild = (not self.tracked_guilds) or (
            message.guild.id in self.tracked_guilds
        )
        if not is_tracked_guild:
            return

        # Check if message is from a tracked channel
        is_tracked_channel = message.channel.id in self.all_tracked_channels
        if not is_tracked_channel:
            return

        # Check if bot is mentioned
        is_bot_mentioned = (
            any(user.id == self.bot_user_id for user in message.mentions)
            or f"<@{self.bot_user_id}>" in message.content
        )

        if is_bot_mentioned:
            message_id = f"discord_{message.guild.id}_{message.channel.id}_{message.id}"

            if not self.is_processed(message_id):
                data = await self.extract_mention_data(message)
                if self.process_mention(message_id, data):
                    self.processed_messages.add(message_id)
                    self.logger.info(
                        f"Processed mention in {message.guild.name} / {message.channel.name}"
                    )

    async def extract_mention_data(self, message):
        """Extract standardized data from Discord message.

        :param message: Discord message object
        :type message: :class:`discord.Message`
        :var author: user who sent the message
        :type author: :class:`discord.User`
        :var referenced_message: message that this message replies to
        :type referenced_message: :class:`discord.Message` or None
        :var channel: channel where message was sent
        :type channel: :class:`discord.TextChannel`
        :var guild: Discord server where message was sent
        :type guild: :class:`discord.Guild`
        :var data: extracted mention data dictionary
        :type data: dict
        :return: standardized mention data
        :rtype: dict
        """
        author = message.author
        referenced_message = message.reference.resolved if message.reference else None
        channel = message.channel
        guild = message.guild

        # Generate message URLs
        message_url = message.jump_url

        if referenced_message and hasattr(referenced_message, "jump_url"):
            contribution_url = referenced_message.jump_url
            contributor = referenced_message.author
        else:
            contribution_url = message_url
            contributor = author

        data = {
            "suggester": author.id,
            "suggester_username": author.name,
            "suggester_display_name": author.display_name,
            "suggestion_url": message_url,
            "contribution_url": contribution_url,
            "contributor": contributor.id,
            "contributor_username": contributor.name,
            "contributor_display_name": contributor.display_name,
            "type": "message",
            "discord_channel": channel.name,
            "discord_guild": guild.name,
            "channel_id": channel.id,
            "guild_id": guild.id,
            "content_preview": message.content[:200] if message.content else "",
            "timestamp": message.created_at.isoformat(),
            "item_id": f"discord_{guild.id}_{channel.id}_{message.id}",
        }

        return data

    async def _check_channel_history(self, channel_id, guild_id):
        """Check historical messages in a specific channel.

        :param channel_id: ID of the channel to check
        :type channel_id: int
        :param guild_id: ID of the guild containing the channel
        :type guild_id: int
        :var channel: Discord channel object
        :type channel: :class:`discord.TextChannel`
        :var mention_count: number of mentions found in this channel
        :type mention_count: int
        :var messages: historical messages from the channel
        :type messages: list of :class:`discord.Message`
        :var message: individual message from channel
        :type message: :class:`discord.Message`
        :var message_id: unique identifier for the message
        :type message_id: str
        :var data: extracted mention data
        :type data: dict
        :return: number of new mentions processed in this channel
        :rtype: int
        """
        # Rate limiting per channel
        now = datetime.now()
        last_check = self.last_channel_check.get(channel_id)

        if last_check and (now - last_check) < timedelta(seconds=self.rate_limit_delay):
            return 0

        self.last_channel_check[channel_id] = now

        mention_count = 0
        channel = self.client.get_channel(channel_id)

        if not channel:
            return 0

        try:
            # Get recent messages
            async for message in channel.history(limit=self.max_messages_per_channel):
                if message.author.bot:
                    continue

                is_bot_mentioned = (
                    any(user.id == self.bot_user_id for user in message.mentions)
                    or f"<@{self.bot_user_id}>" in message.content
                )

                if is_bot_mentioned:
                    message_id = f"discord_{guild_id}_{channel.id}_{message.id}"

                    if not self.is_processed(message_id):
                        data = await self.extract_mention_data(message)
                        if self.process_mention(message_id, data):
                            mention_count += 1
                            self.processed_messages.add(message_id)

        except HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_after = e.retry_after if hasattr(e, "retry_after") else 5
                self.logger.warning(
                    f"Rate limited on channel {channel_id}, retrying in {retry_after}s"
                )
                await asyncio.sleep(retry_after)
            else:
                self.logger.error(f"HTTP error checking channel {channel_id}: {e}")

        except Forbidden:
            self.logger.warning(f"No permission to access channel {channel_id}")
            # Remove channel from tracking
            if (
                guild_id in self.guild_channels
                and channel_id in self.guild_channels[guild_id]
            ):
                self.guild_channels[guild_id].remove(channel_id)
                self._update_all_tracked_channels()

        except Exception as e:
            self.logger.error(f"Error checking channel {channel_id}: {e}")

        return mention_count

    async def check_mentions_async(self):
        """Asynchronously check for new mentions across all tracked channels in all guilds.

        :var total_mentions: total number of new mentions found
        :type total_mentions: int
        :var semaphore: semaphore for limiting concurrent channel checks
        :type semaphore: :class:`asyncio.Semaphore`
        :var tasks: list of channel check tasks
        :type tasks: list of :class:`asyncio.Task`
        :var channel_mentions: mentions from individual channel checks
        :type channel_mentions: list of int
        """
        if not self.client.is_ready():
            return 0

        total_mentions = 0

        # Limit concurrent channel checks
        semaphore = asyncio.Semaphore(self.concurrent_channel_checks)

        async def check_channel_with_semaphore(channel_id, guild_id):
            async with semaphore:
                return await self._check_channel_history(channel_id, guild_id)

        # Create tasks for all channels across all guilds
        tasks = []
        for guild_id, channel_ids in self.guild_channels.items():
            for channel_id in channel_ids:
                tasks.append(check_channel_with_semaphore(channel_id, guild_id))

        # Process channels concurrently with limits
        channel_mentions = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        for i, result in enumerate(channel_mentions):
            if isinstance(result, Exception):
                self.logger.error(f"Error processing channel: {result}")
            else:
                total_mentions += result

        return total_mentions

    async def run_continuous(self, token, historical_check_interval=300):
        """Run Discord tracker in continuous mode with periodic historical checks.

        :param token: Discord bot token
        :type token: str
        :param historical_check_interval: how often to run historical checks (seconds)
        :type historical_check_interval: int
        :var last_historical_check: timestamp of last historical check
        :type last_historical_check: :class:`datetime.datetime`
        :var last_channel_discovery: timestamp of last channel discovery
        :type last_channel_discovery: :class:`datetime.datetime`
        :var mentions_found: number of mentions found in historical check
        :type mentions_found: int
        """
        self.logger.info("Starting multi-guild Discord tracker in continuous mode")
        self.log_action("started", "Continuous multi-guild mode")

        last_historical_check = datetime.now()
        last_channel_discovery = datetime.now()

        try:
            await self.client.start(token)

            # Keep the bot running and perform periodic tasks
            while not self.client.is_closed():
                now = datetime.now()

                # Periodic channel discovery
                if (now - last_channel_discovery) > timedelta(
                    seconds=self.channel_discovery_interval
                ):
                    self.logger.info("Running periodic channel discovery")
                    await self._discover_all_guild_channels()
                    last_channel_discovery = now

                # Periodic historical checks
                if (now - last_historical_check) > timedelta(
                    seconds=historical_check_interval
                ):
                    self.logger.info("Running periodic historical check")
                    mentions_found = await self.check_mentions_async()
                    if mentions_found > 0:
                        self.logger.info(
                            f"Found {mentions_found} new mentions in historical check"
                        )
                    last_historical_check = now

                # Small sleep to prevent busy waiting
                await asyncio.sleep(10)

        except KeyboardInterrupt:
            self.logger.info("Multi-guild Discord tracker stopped by user")
            self.log_action("stopped", "User interrupt")
        except Exception as e:
            self.logger.error(f"Multi-guild Discord tracker error: {e}")
            self.log_action("error", f"Tracker error: {str(e)}")
            raise
        finally:
            await self.client.close()
            self.cleanup()

    def get_stats(self):
        """Get statistics about the current tracking state.

        :var stats: dictionary containing tracking statistics
        :type stats: dict
        :return: tracking statistics
        :rtype: dict
        """
        stats = {
            "guilds_tracked": len(self.guild_channels),
            "channels_tracked": len(self.all_tracked_channels),
            "processed_messages": len(self.processed_messages),
            "guild_details": {},
        }

        for guild_id, channel_ids in self.guild_channels.items():
            guild = self.client.get_guild(guild_id)
            guild_name = guild.name if guild else f"Unknown ({guild_id})"
            stats["guild_details"][guild_name] = len(channel_ids)

        return stats
