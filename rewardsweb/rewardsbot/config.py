import os

from dotenv import load_dotenv

load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
GUILD_IDS = os.getenv("DISCORD_GUILD_IDS")
BASE_URL = os.getenv("REWARDS_API_BASE_URL")
