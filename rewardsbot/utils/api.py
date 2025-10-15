import aiohttp
import logging

from config import BASE_URL

logger = logging.getLogger("discord.api")


class ApiService:
    def __init__(self):
        self.session = None

    async def initialize(self):
        """Initialize the aiohttp session"""
        logger.info("🔗 Initializing API service...")
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Content-Type": "application/json"},
        )
        logger.info("✅ API service initialized")

    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            logger.info("✅ API service closed")

    async def make_request(self, endpoint, params=None, method="GET"):
        if params is None:
            params = {}

        url = f"{BASE_URL}/{endpoint}"
        logger.info(f"🌐 API Request: {method} {url} with params: {params}")

        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    logger.info(f"📡 API Response Status: {response.status} for {url}")
                    response.raise_for_status()
                    data = await response.json()
                    logger.info(
                        f"✅ API Response received for {endpoint}: {len(str(data))} bytes"
                    )
                    return data
            else:
                async with self.session.post(url, json=params) as response:
                    logger.info(f"📡 API Response Status: {response.status} for {url}")
                    response.raise_for_status()
                    data = await response.json()
                    logger.info(
                        f"✅ API Response received for {endpoint}: {len(str(data))} bytes"
                    )
                    return data

        except aiohttp.ClientError as error:
            logger.error(f"❌ API Request error for {endpoint}: {error}")
            raise
        except Exception as error:
            logger.error(f"❌ Unexpected API error for {endpoint}: {error}")
            raise

    # Your existing methods...
    async def fetch_current_cycle(self):
        logger.info("🔗 fetch_current_cycle called")
        return await self.make_request("cycles/current")

    async def fetch_current_cycle_plain(self):
        logger.info("🔗 fetch_current_cycle_plain called")
        return await self.make_request("cycles/current-plain")

    async def fetch_cycle_by_id(self, cycle_id):
        logger.info(f"🔗 fetch_cycle_by_id called for cycle {cycle_id}")
        return await self.make_request(f"cycles/{cycle_id}")

    async def fetch_contributions_tail(self):
        logger.info("🔗 fetch_contributions_tail called")
        return await self.make_request("contributions/tail")

    async def fetch_user_contributions(self, username):
        logger.info(f"🔗 fetch_user_contributions called for {username}")
        return await self.make_request("contributions", {"name": username})

    async def post_suggestion(self, contribution_type, level, username, message_url):
        logger.info(f"🔗 post_suggestion called for {username}")
        return await self.make_request(
            "addcontribution",
            {
                "type": contribution_type,
                "level": level,
                "name": username,
                "url": message_url,
                "platform": "Discord",
            },
            "POST",
        )
