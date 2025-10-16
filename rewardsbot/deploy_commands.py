import asyncio
import discord
from discord import app_commands
from typing import Optional

import config


class CommandDeployer:
    def __init__(self):
        self.intents = discord.Intents.default()
        self.bot = discord.Client(intents=self.intents)
        self.tree = app_commands.CommandTree(self.bot)

        self.setup_commands()

    def setup_commands(self):
        # Create command group (matching bot.py structure)
        rewards_group = app_commands.Group(
            name="rewards", description="Manage rewards and contributions"
        )
        self.tree.add_command(rewards_group)

        # Cycle subcommands
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

        # User subcommand
        @rewards_group.command(name="user", description="Get user contributions")
        @app_commands.describe(username="Username to fetch data for")
        async def rewards_user(interaction: discord.Interaction, username: str):
            """User subcommand"""
            pass

        # Suggest subcommand
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
            """Suggest subcommand"""
            pass

        # Context menu command
        @self.tree.context_menu(name="Suggest Reward")
        async def suggest_reward_context(
            interaction: discord.Interaction, message: discord.Message
        ):
            """Context menu for suggesting rewards on messages"""
            pass

    async def deploy(self):
        @self.bot.event
        async def on_ready():
            print(f"✅ Logged in as {self.bot.user}")

            try:
                # Sync global commands
                global_commands = await self.tree.sync()
                print(f"✅ Synced {len(global_commands)} global command(s)")

                # Sync to specific guild if configured
                if hasattr(config, "GUILD_ID") and config.GUILD_ID:
                    guild = discord.Object(id=config.GUILD_ID)
                    guild_commands = await self.tree.sync(guild=guild)
                    print(
                        f"✅ Synced {len(guild_commands)} command(s) to guild {config.GUILD_ID}"
                    )

                # Print command structure for verification
                print("\n📋 Command Structure:")
                for command in global_commands:
                    if isinstance(command, app_commands.Group):
                        print(f"  └── /{command.name} (Group)")
                        # Note: Subcommands might not be visible at this level in this context
                    else:
                        print(f"  └── /{command.name}")

            except Exception as e:
                print(f"❌ Command sync error: {e}")
            finally:
                # Ensure clean shutdown
                await self.bot.close()

        try:
            await self.bot.start(config.DISCORD_TOKEN)
        except discord.LoginFailure:
            print("❌ Invalid token")
        except Exception as e:
            print(f"❌ Deployment failed: {e}")


async def main():
    print("🚀 Starting command deployment...")
    print("📝 This will deploy the command structure to Discord's servers")
    print("🕒 This may take up to 1 hour to propagate globally")
    deployer = CommandDeployer()
    await deployer.deploy()
    print("✅ Deployment completed successfully!")
    print("📋 Commands should appear in your server within the hour")
    print("\n🎯 Cycle command usage examples:")
    print("  /rewards current")
    print("  /rewards date")
    print("  /rewards contributions")
    print("  /rewards cycle 40")


if __name__ == "__main__":
    asyncio.run(main())
