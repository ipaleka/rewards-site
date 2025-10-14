import discord
from discord import app_commands
import asyncio
import config

class CommandDeployer:
    def __init__(self):
        self.intents = discord.Intents.default()
        self.bot = discord.Client(intents=self.intents)
        self.tree = app_commands.CommandTree(self.bot)
        
        self.setup_commands()

    def setup_commands(self):
        @self.tree.command(name="rewards", description="Manage rewards")
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
            pass

        @self.tree.context_menu(name="Suggest Reward")
        async def suggest_context(interaction: discord.Interaction, message: discord.Message):
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
                if hasattr(config, 'GUILD_ID') and config.GUILD_ID:
                    guild = discord.Object(id=config.GUILD_ID)
                    guild_commands = await self.tree.sync(guild=guild)
                    print(f"✅ Synced {len(guild_commands)} command(s) to guild {config.GUILD_ID}")
                    
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
    deployer = CommandDeployer()
    await deployer.deploy()
    print("✅ Deployment completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())