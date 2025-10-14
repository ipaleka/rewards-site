import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
BASE_URL = os.getenv("API_BASE_URL")
