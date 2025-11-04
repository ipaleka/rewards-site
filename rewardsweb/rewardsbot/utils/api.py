"""API service for handling HTTP requests to the rewards backend.

This module provides the ApiService class for making HTTP requests
to the rewards backend API with proper session management and error handling.

:var logger: API service logger instance
:type logger: :class:`logging.Logger`
"""

import logging

import aiohttp
from aiohttp import ClientSession

from rewardsbot.config import BASE_URL

logger = logging.getLogger("discord.api")


class ApiService:
    """Service class for API interactions with the rewards backend.

    This class manages HTTP sessions and provides methods for all
    API endpoints used by the rewards bot.

    :ivar session: aiohttp client session for making requests
    :type session: :class:`aiohttp.ClientSession` or None
    """

    def __init__(self):
        """Initialize ApiService without an active session."""
        self.session = None

    async def initialize(self):
        """Initialize the aiohttp session.

        Creates a new ClientSession with timeout and header configuration.
        """
        logger.info("🔗 Initializing API service...")
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Content-Type": "application/json"},
        )
        logger.info("✅ API service initialized")

    async def close(self):
        """Close the aiohttp session.

        Safely closes the session if it exists.
        """
        if self.session:
            await self.session.close()
            logger.info("✅ API service closed")

    async def make_request(self, endpoint, params=None, method="GET"):
        """Make an HTTP request to the API.

        :param endpoint: API endpoint to call (without base URL)
        :type endpoint: str
        :param params: Query parameters for GET or JSON data for POST
        :type params: dict or None
        :param method: HTTP method (GET or POST)
        :type method: str
        :return: JSON response from the API
        :rtype: dict or list
        :raises aiohttp.ClientError: For HTTP-related errors
        :raises Exception: For other unexpected errors
        """
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

        except Exception as error:
            logger.error(f"❌ Unexpected API error for {endpoint}: {error}")
            raise

    async def fetch_cycle(self, cycle_number):
        """Fetch cycle data by cycle number.

        :param cycle_number: The cycle number to fetch
        :type cycle_number: int or str
        :return: Cycle data
        :rtype: dict
        """
        logger.info("🔗 fetch_cycle called")
        return await self.make_request(f"cycles/{cycle_number}")

    async def fetch_current_cycle(self):
        """Fetch current cycle data.

        :return: Current cycle data
        :rtype: dict
        """
        logger.info("🔗 fetch_current_cycle called")
        return await self.make_request("cycles/current")

    async def fetch_current_cycle_plain(self):
        """Fetch current cycle data in plain format.

        :return: Current cycle data in plain format
        :rtype: dict
        """
        logger.info("🔗 fetch_current_cycle_plain called")
        return await self.make_request("cycles/current/plain")

    async def fetch_cycle_by_id(self, cycle_id):
        """Fetch cycle data by cycle ID.

        :param cycle_id: The cycle ID to fetch
        :type cycle_id: int or str
        :return: Cycle data
        :rtype: dict
        """
        logger.info(f"🔗 fetch_cycle_by_id called for cycle {cycle_id}")
        return await self.make_request(f"cycles/{cycle_id}")

    async def fetch_cycle_by_id_plain(self, cycle_id):
        """Fetch cycle data by cycle ID in plain format.

        :param cycle_id: The cycle ID to fetch
        :type cycle_id: int or str
        :return: Cycle data in plain format
        :rtype: dict
        """
        logger.info(f"🔗 fetch_cycle_by_id_plain called for cycle {cycle_id}")
        return await self.make_request(f"cycles/{cycle_id}/plain")

    async def fetch_contributions_tail(self):
        """Fetch the most recent contributions.

        :return: List of recent contributions
        :rtype: list
        """
        logger.info("🔗 fetch_contributions_tail called")
        return await self.make_request("contributions/tail")

    async def fetch_user_contributions(self, username):
        """Fetch contributions for a specific user.

        :param username: Username to fetch contributions for
        :type username: str
        :return: List of user contributions
        :rtype: list
        """
        logger.info(f"🔗 fetch_user_contributions called for {username}")
        return await self.make_request("contributions", {"name": username})

    async def post_suggestion(
        self, contribution_type, level, username, comment, message_url
    ):
        """Post a new contribution suggestion.

        :param contribution_type: Type of contribution
        :type contribution_type: str
        :param level: Contribution level (1-3)
        :type level: str
        :param username: Contributor username
        :type username: str
        :param comment: Additional comment about the contribution
        :type comment: str
        :param message_url: URL of the Discord message
        :type message_url: str
        :return: API response from suggestion creation
        :rtype: dict
        """
        logger.info(f"🔗 post_suggestion called for {username}")
        return await self.make_request(
            "addcontribution",
            {
                "type": contribution_type,
                "level": level,
                "username": username,
                "comment": comment,
                "url": message_url,
                "platform": "Discord",
            },
            "POST",
        )
