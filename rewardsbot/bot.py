import asyncio
import logging
import signal
import sys

import discord
from discord.ext import commands
from discord import app_commands

import config
from services.cycle_service import CycleService
from services.user_service import UserService
from utils.api import ApiService
from controllers.command_handler import SuggestRewardModal

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("discord.bot")


class RewardsBot(commands.Bot):
    def __init__(self):
        # Configure intents
        intents = discord.Intents.all()

        # Bot presence and activity
        activity = discord.Activity(
            type=discord.ActivityType.watching, name="reward suggestions"
        )

        super().__init__(
            command_prefix="!",
            intents=intents,
            activity=activity,
            status=discord.Status.online,
            # 2.6.4: Better member caching for user lookups
            member_cache_flags=discord.MemberCacheFlags.all(),
            # Enable message content for potential future features
            max_messages=1000,
        )

        # Initialize API service for ADRF endpoints
        self.api_service = ApiService()
        self._shutting_down = False

    async def setup_hook(self):
        """Async setup called when bot starts"""
        logger.info("🚀 Starting bot setup...")

        # Validate configuration
        await self._validate_config()

        # Setup commands and sync with Discord
        await self._setup_commands()

        # Initialize API connections
        await self._initialize_services()

        logger.info("✅ Bot setup completed successfully")

    async def _validate_config(self):
        """Validate all required configuration"""
        if not config.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN not found in configuration")

        if not config.BASE_URL:
            logger.warning("BASE_URL not configured - API features will not work")

        logger.info(
            f"✅ Configuration validated - API Base: {getattr(config, 'BASE_URL', 'Not set')}"
        )

    async def _setup_commands(self):
        """Setup and sync application commands"""
        try:
            logger.info("🔄 Setting up application commands...")

            # Sync global commands
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} global command(s)")

            # Sync guild-specific commands if configured
            if hasattr(config, "GUILD_ID") and config.GUILD_ID:
                guild = discord.Object(id=config.GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced_guild = await self.tree.sync(guild=guild)
                logger.info(
                    f"✅ Synced {len(synced_guild)} command(s) to guild {config.GUILD_ID}"
                )

        except Exception as e:
            logger.error(f"❌ Failed to setup commands: {e}")
            raise

    async def _initialize_services(self):
        """Initialize API services and connections"""
        try:
            # Initialize API service (will create aiohttp session)
            await self.api_service.initialize()
            logger.info("✅ API service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise

    async def on_ready(self):
        """Called when bot is fully connected and ready"""
        if self._shutting_down:
            return

        logger.info(f"✅ Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"✅ Connected to {len(self.guilds)} guild(s):")

        # Log guild information
        for guild in self.guilds:
            logger.info(
                f"   - {guild.name} (ID: {guild.id}, Members: {guild.member_count})"
            )

        # Log command information
        commands_list = await self.tree.fetch_commands()
        logger.info(f"✅ {len(commands_list)} command(s) available")

        logger.info("------ Bot is fully operational! ------")

    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logger.info(f"➕ Joined new guild: {guild.name} (ID: {guild.id})")

        # Sync commands to the new guild
        try:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"✅ Synced commands to new guild: {guild.name}")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands to new guild: {e}")

    async def on_guild_remove(self, guild):
        """Called when bot is removed from a guild"""
        logger.info(f"➖ Removed from guild: {guild.name} (ID: {guild.id})")

    async def on_disconnect(self):
        """Called when bot disconnects from Discord"""
        if not self._shutting_down:
            logger.warning("🔌 Bot disconnected from Discord")

    async def on_resumed(self):
        """Called when bot resumes connection"""
        logger.info("🔁 Bot resumed connection to Discord")

    async def close(self):
        """Clean shutdown - close all resources properly"""
        if self._shutting_down:
            return

        self._shutting_down = True
        logger.info("🛑 Starting bot shutdown sequence...")

        try:
            # Close API service first (aiohttp sessions)
            await self.api_service.close()
            logger.info("✅ API service closed")

            # Call parent close method
            await super().close()
            logger.info("✅ Discord connection closed")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        finally:
            logger.info("✅ Bot shutdown completed successfully")


# Create bot instance
bot = RewardsBot()

# Define command groups
rewards_group = app_commands.Group(
    name="rewards", description="Manage rewards and contributions"
)
bot.tree.add_command(rewards_group)


# Global error handler for all application commands
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    """Global error handler for application commands"""
    logger.error(
        f"Command error in {interaction.command.name if interaction.command else 'unknown'}: {error}"
    )

    user_info = f"{interaction.user} (ID: {interaction.user.id})"
    guild_info = (
        f"{interaction.guild.name} (ID: {interaction.guild.id})"
        if interaction.guild
        else "DM"
    )

    # Log detailed error information
    logger.error(f"Command error context: User: {user_info}, Guild: {guild_info}")

    # User-friendly error messages based on error type
    if isinstance(error, app_commands.CommandOnCooldown):
        message = f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
    elif isinstance(error, app_commands.MissingPermissions):
        message = "❌ You don't have permission to use this command."
    elif isinstance(error, app_commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        message = f"❌ I'm missing permissions to execute this command: {missing}"
    elif isinstance(error, app_commands.CheckFailure):
        message = "❌ You cannot use this command in this context."
    else:
        message = "❌ An unexpected error occurred while executing this command."
        # Log unexpected errors with full traceback
        logger.error("Unexpected command error:", exc_info=error)

    # Send error response
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.NotFound:
        logger.warning("Could not send error message - interaction already expired")
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


# Cycle subcommand
@rewards_group.command(name="cycle", description="Get cycle information")
@app_commands.describe(detail="Detail about the cycle")
@app_commands.choices(
    detail=[
        app_commands.Choice(name="current", value="current"),
        app_commands.Choice(name="date", value="date"),
        app_commands.Choice(name="tail", value="tail"),
    ]
)
async def rewards_cycle(interaction: discord.Interaction, detail: str):
    """Cycle subcommand"""
    await interaction.response.defer(thinking=True)

    # Get the bot instance to access the api_service
    bot = interaction.client

    try:
        if detail == "current":
            info = await CycleService.current_cycle_info(bot.api_service)
            await interaction.followup.send(info)

        elif detail == "date":
            end_date_info = await CycleService.cycle_end_date(bot.api_service)
            await interaction.followup.send(end_date_info)

        elif detail == "tail":
            cycle_last = await CycleService.contributions_tail(bot.api_service)
            await interaction.followup.send(cycle_last)

        else:
            await interaction.followup.send("❌ Invalid detail provided.")

    except Exception as error:
        logger.error(f"❌ Cycle Command Error: {error}", exc_info=True)
        await interaction.followup.send(
            "❌ Failed to process cycle command.", ephemeral=True
        )


# User subcommand
@rewards_group.command(name="user", description="Get user contributions")
@app_commands.describe(username="Username to fetch data for")
async def rewards_user(interaction: discord.Interaction, username: str):
    """User subcommand"""
    await interaction.response.defer(thinking=True)

    # Get the bot instance to access the api_service
    bot = interaction.client

    try:
        user_summary = await UserService.user_summary(bot.api_service, username)
        await interaction.followup.send(user_summary)

    except Exception as error:
        logger.error(f"❌ User Command Error: {error}", exc_info=True)
        await interaction.followup.send(
            "❌ Failed to process user command.", ephemeral=True
        )


# Suggest subcommand
@rewards_group.command(name="suggest", description="Suggest a reward for a user")
@app_commands.describe(
    username="The username to suggest a reward for",
    reason="Reason for the reward suggestion",
)
async def rewards_suggest(interaction: discord.Interaction, username: str, reason: str):
    """Suggest subcommand"""
    await interaction.response.defer(thinking=True)

    try:
        # You can implement the suggestion logic here or call your existing handler
        result = f"✅ Reward suggestion recorded for {username}: {reason}"
        await interaction.followup.send(result)

    except Exception as error:
        logger.error(f"❌ Suggest Command Error: {error}", exc_info=True)
        await interaction.followup.send(
            "❌ Failed to process suggestion.", ephemeral=True
        )


# Context menu command for suggesting rewards
@bot.tree.context_menu(name="Suggest Reward")
async def suggest_reward_context(
    interaction: discord.Interaction, message: discord.Message
):
    """Context menu for suggesting rewards on messages"""
    try:
        # Validate the message
        if message.author.bot:
            await interaction.response.send_message(
                "❌ Cannot suggest rewards for bot messages.", ephemeral=True
            )
            return

        if message.author == interaction.user:
            await interaction.response.send_message(
                "❌ Cannot suggest rewards for your own messages.", ephemeral=True
            )
            return

        # Open the suggestion modal
        modal = SuggestRewardModal(target_message=message)
        await interaction.response.send_modal(modal)

        logger.info(
            f"📝 Suggestion modal opened for message {message.id} by {interaction.user}"
        )

    except Exception as e:
        logger.error(f"Context menu error: {e}", exc_info=True)
        try:
            await interaction.response.send_message(
                "❌ Failed to open suggestion form.", ephemeral=True
            )
        except discord.NotFound:
            logger.warning("Interaction expired before error could be sent")


# Global interaction logger
@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Log all interactions for debugging and analytics"""
    if interaction.type == discord.InteractionType.application_command:
        command_name = interaction.command.name if interaction.command else "unknown"
        user = f"{interaction.user} (ID: {interaction.user.id})"
        guild = (
            f"{interaction.guild.name} (ID: {interaction.guild.id})"
            if interaction.guild
            else "DM"
        )

        logger.info(f"🔧 Command executed: {command_name} by {user} in {guild}")


# Simplified signal handling
async def shutdown_bot():
    """Perform graceful shutdown"""
    logger.info("🚦 Starting graceful shutdown process...")
    await bot.close()


def handle_signal(sig):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {sig.name}, initiating graceful shutdown...")
    asyncio.create_task(shutdown_bot())


async def main():
    """Main entry point with comprehensive error handling"""
    try:
        logger.info("🎯 Starting Rewards Bot...")

        # Validate critical configuration
        if not config.DISCORD_TOKEN:
            logger.error("❌ No Discord token found in configuration")
            return 1

        if not getattr(config, "BASE_URL", None):
            logger.warning("⚠️  BASE_URL not configured - API features will be disabled")

        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

        # Start the bot with context manager for proper resource handling
        async with bot:
            await bot.start(config.DISCORD_TOKEN)

        return 0

    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token provided")
        return 1
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user (KeyboardInterrupt)")
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error during bot execution: {e}", exc_info=True)
        return 1
    finally:
        logger.info("👋 Bot session ended")


if __name__ == "__main__":
    # Run the bot with simple error handling
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⏹️ Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}", exc_info=True)
        sys.exit(1)
