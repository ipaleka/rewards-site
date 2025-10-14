import aiohttp
from config import BASE_URL


class ApiService:
    @staticmethod
    async def make_request(endpoint, params=None, method="GET"):
        if params is None:
            params = {}

        url = f"{BASE_URL}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                if method.upper() == "GET":
                    async with session.get(url, params=params) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, json=params) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as error:
                print(f"Error making {method} request to {endpoint}: {error}")
                raise error

    @staticmethod
    async def fetch_cycle_current():
        return await ApiService.make_request("cycles/aggregated")

    @staticmethod
    async def fetch_cycle_dates(cycle_id):
        return await ApiService.make_request(f"cycles/dates/{cycle_id}")

    @staticmethod
    async def fetch_cycle_last():
        return await ApiService.make_request("contributions/last")

    @staticmethod
    async def fetch_user_contributions(username):
        return await ApiService.make_request("contributions", {"name": username})

    @staticmethod
    async def post_suggestion(contribution_type, level, username, message_url):
        return await ApiService.make_request(
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
