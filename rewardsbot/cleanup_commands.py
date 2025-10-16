import asyncio
from typing import Optional

import discord
from discord import app_commands

import config


class CommandCleanup:
    def __init__(self):
        self.intents = discord.Intents.default()
        self.bot = discord.Client(intents=self.intents)
        self.tree = app_commands.CommandTree(self.bot)

    async def cleanup(self):
        @self.bot.event
        async def on_ready():
            print(f"✅ Logged in as {self.bot.user}")

            try:
                # Method 1: Clear ALL commands and resync
                print("🔄 Clearing all commands...")

                # First, get current commands
                current_commands = await self.tree.fetch_commands()
                print(f"📋 Found {len(current_commands)} current global command(s)")

                for cmd in current_commands:
                    print(f"  - {cmd.name} (ID: {cmd.id})")

                # Clear the entire command tree
                self.tree.clear_commands(guild=None)

                # Sync empty commands first (this removes everything)
                await self.tree.sync()
                print("✅ Cleared all global commands")

                # Now redeploy the correct commands
                await self.deploy_correct_commands()

            except Exception as e:
                print(f"❌ Cleanup error: {e}")
            finally:
                await self.bot.close()

        try:
            await self.bot.start(config.DISCORD_TOKEN)

        except Exception as e:
            print(f"❌ Cleanup failed: {e}")

    async def deploy_correct_commands(self):
        """Deploy the correct command structure"""
        # Create the proper command group structure
        rewards_group = app_commands.Group(
            name="rewards", description="Manage rewards and contributions"
        )
        self.tree.add_command(rewards_group)

        # Add subcommands
        @rewards_group.command(
            name="current", description="Get current cycle information"
        )
        async def rewards_cycle_current(interaction: discord.Interaction):
            pass

        @rewards_group.command(name="date", description="Get cycle end date")
        async def rewards_cycle_date(interaction: discord.Interaction):
            pass

        @rewards_group.command(
            name="contributions", description="Get recent contributions"
        )
        async def rewards_contributions_tail(interaction: discord.Interaction):
            pass

        @rewards_group.command(
            name="cycle", description="Get specific cycle information by number"
        )
        @app_commands.describe(number="The cycle number to look up")
        async def rewards_cycle_specific(interaction: discord.Interaction, number: int):
            pass

        @rewards_group.command(name="user", description="Get user contributions")
        @app_commands.describe(username="Username to fetch data for")
        async def rewards_user(interaction: discord.Interaction, username: str):
            pass

        @rewards_group.command(
            name="suggest", description="Suggest a reward for a user"
        )
        @app_commands.describe(
            username="The username to suggest a reward for",
            reason="Reason for the reward suggestion",
        )
        async def rewards_suggest(
            interaction: discord.Interaction, username: str, reason: str
        ):
            pass

        # Context menu
        @self.tree.context_menu(name="Suggest Reward")
        async def suggest_reward_context(
            interaction: discord.Interaction, message: discord.Message
        ):
            pass

        # Sync the corrected commands
        synced = await self.tree.sync()
        print(f"✅ Redeployed {len(synced)} correct command(s)")

        # Also cleanup guild-specific commands if used
        if hasattr(config, "GUILD_ID") and config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)

            # Redeploy to guild
            self.tree.copy_global_to(guild=guild)
            guild_synced = await self.tree.sync(guild=guild)
            print(
                f"✅ Redeployed {len(guild_synced)} command(s) to guild {config.GUILD_ID}"
            )


async def main():
    print("🧹 Starting command cleanup...")
    print("⚠️  This will remove ALL commands and redeploy the correct structure")
    cleanup = CommandCleanup()
    await cleanup.cleanup()
    print("✅ Cleanup completed! Old commands should be removed.")
    print("📝 Note: It may take up to 1 hour for changes to propagate globally")


if __name__ == "__main__":
    asyncio.run(main())
