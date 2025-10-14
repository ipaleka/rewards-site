import discord
from discord.ext import commands
from discord import app_commands
import config
import asyncio
import logging
from controllers.command_handler import handle_slash_command

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('discord.bot')

class RewardsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        
        # 2.6.4: Using latest activity and status features
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="reward suggestions"
        )
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            activity=activity,
            status=discord.Status.online
        )
        
    async def setup_hook(self):
        """Called when the bot is starting up - perfect for initial setup"""
        logger.info("Starting bot setup...")
        
        # Register custom checks or global commands here
        await self.load_extension_commands()
        await self.sync_commands()
        
    async def load_extension_commands(self):
        """Load command handlers if using extensions"""
        try:
            # If you want to use cogs/extensions in the future
            # await self.load_extension('cogs.rewards')
            pass
        except Exception as e:
            logger.error(f"Failed to load extensions: {e}")

    async def sync_commands(self):
        """Sync application commands with Discord"""
        try:
            logger.info("Syncing application commands...")
            
            # Sync global commands
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} global command(s)")
            
            # Sync guild-specific commands if configured
            if config.GUILD_ID:
                guild = discord.Object(id=config.GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced_guild = await self.tree.sync(guild=guild)
                logger.info(f"✅ Synced {len(synced_guild)} command(s) to guild {config.GUILD_ID}")
                
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is fully connected and ready"""
        logger.info(f'✅ Logged in as {self.user.name} (ID: {self.user.id})')
        logger.info(f'✅ Connected to {len(self.guilds)} guild(s):')
        
        for guild in self.guilds:
            logger.info(f'   - {guild.name} (ID: {guild.id})')
            
        logger.info('------ Bot is ready! ------')

    async def on_disconnect(self):
        """Called when the bot disconnects from Discord"""
        logger.warning("🔌 Bot disconnected from Discord")

    async def on_resumed(self):
        """Called when the bot resumes connection"""
        logger.info("🔁 Bot resumed connection")

    async def close(self):
        """Called when the bot is closing - cleanup resources"""
        logger.info("🛑 Shutting down bot...")
        
        # Close any database connections or other resources here
        # await self.db.close() if you have a database
        
        await super().close()
        logger.info("✅ Bot shutdown complete")

# Create bot instance
bot = RewardsBot()

# Global error handler for all commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for application commands"""
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.", 
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", 
            ephemeral=True
        )
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message(
            f"❌ I'm missing permissions to execute this command: {error.missing_permissions}", 
            ephemeral=True
        )
    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ You cannot use this command.", 
            ephemeral=True
        )
    else:
        logger.error(f"Command error in {interaction.command.name}: {error}", exc_info=True)
        
        # Only send error message if we haven't responded yet
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ An unexpected error occurred while executing this command.", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ An unexpected error occurred while executing this command.", 
                ephemeral=True
            )

# Slash command with better organization and error handling
@bot.tree.command(name="rewards", description="Manage rewards and contributions")
@app_commands.describe(
    subcommand="Choose an action",
    username="The username to check contributions for",
    detail="Detail about the cycle"
)
@app_commands.choices(subcommand=[
    app_commands.Choice(name="cycle", value="cycle"),
    app_commands.Choice(name="user", value="user"), 
    app_commands.Choice(name="suggest", value="suggest")
])
@app_commands.choices(detail=[
    app_commands.Choice(name="current", value="current"),
    app_commands.Choice(name="end", value="end"),
    app_commands.Choice(name="last", value="last")
])
async def rewards_command(
    interaction: discord.Interaction, 
    subcommand: app_commands.Choice[str],
    username: str = None,
    detail: app_commands.Choice[str] = None
):
    """Main rewards command handler"""
    await handle_slash_command(interaction)

# Context menu command with better error handling
@bot.tree.context_menu(name="Suggest Reward")
async def suggest_reward_context(interaction: discord.Interaction, message: discord.Message):
    """Context menu for suggesting rewards on messages"""
    try:
        from controllers.command_handler import SuggestRewardModal
        
        # Validate that we're not suggesting rewards for bots
        if message.author.bot:
            await interaction.response.send_message(
                "❌ Cannot suggest rewards for bot messages.", 
                ephemeral=True
            )
            return
            
        modal = SuggestRewardModal(target_message=message)
        await interaction.response.send_modal(modal)
        
    except Exception as e:
        logger.error(f"Context menu error: {e}", exc_info=True)
        await interaction.response.send_message(
            "❌ Failed to open suggestion form.", 
            ephemeral=True
        )

# Handle other interaction types
@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Global interaction handler - useful for logging"""
    if interaction.type == discord.InteractionType.application_command:
        logger.info(
            f"Command executed: {interaction.command.name} by "
            f"{interaction.user} (ID: {interaction.user.id}) in "
            f"{interaction.guild.name if interaction.guild else 'DM'}"
        )

# Graceful shutdown handling
def handle_shutdown(signal_name):
    """Handle shutdown signals gracefully"""
    def signal_handler(sig, frame):
        logger.info(f"Received {signal_name}, shutting down gracefully...")
        asyncio.create_task(bot.close())
    return signal_handler

async def main():
    """Main entry point with proper error handling"""
    try:
        logger.info("🚀 Starting rewards bot...")
        
        # Validate token
        if not config.DISCORD_TOKEN:
            logger.error("❌ No Discord token found in configuration")
            return
            
        # Start the bot
        async with bot:
            await bot.start(config.DISCORD_TOKEN)
            
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token provided")
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
    finally:
        logger.info("👋 Bot session ended")

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    import signal
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_shutdown(sig.name))
    
    # Run the bot
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Script interrupted by user")
    finally:
        loop.close()