# version 0.1 (20241106)
import logging
import aiohttp
import socket
from .const import SERVER_URL

_LOGGER = logging.getLogger(__name__)


class ESP_Device():

    def __init__(self, unique_id: str, token: str):
        self._unique_id = unique_id
        self._token = token

    async def api_request(self, endpoint: str, method: str, json_data: dict | None = None):
        if method not in ["GET", "POST"]:
            raise InvalidMethod

        if not json_data:
            json_data = {}

        async with aiohttp.ClientSession() as session:
            try:
                _LOGGER.error(f"Request: {endpoint} ({method}) {json_data} to: {SERVER_URL}/api/{endpoint}/{self._unique_id}/{self._token}")
                async with session.request(method, f"{SERVER_URL}/api/{endpoint}/{self._unique_id}/{self._token}",
                                           json=json_data, timeout=5.0) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 503:
                        raise DeviceUnavailable("Device is not responding to relay.")
                    else:
                        raise APIError("API returned non 200/503 code")
            except Exception as error:
                _LOGGER.error(f"Error connecting to API. Error: {error}")
                raise ConnectionError

    @property
    async def system_info(self):
        '''Получение системной информации от устройства'''
        data = await self.api_request("system_info", "GET")
        return data

    @property
    async def status(self):
        '''Получение самого последнего статуса'''
        data = await self.api_request("status", "GET")
        return data

    @property
    async def version(self):
        '''Получение версии'''
        data = await self.system_info
        return data.get("fw_version", 0)

    @property
    async def device_type(self):
        '''Получение типа устройства'''
        data = await self.system_info
        return data.get("device_type", "")

    @property
    async def unique_id(self):
        '''Получение unique_id'''
        return self._unique_id

    @property
    async def token(self):
        '''Получение token'''
        return self._token


class InvalidData(Exception):
    """Error to indicate there is an invalid token or unique_id."""


class InvalidMethod(Exception):
    """Error to indicate there is an invalid method."""


class APIError(Exception):
    """Error to indicate there is an error in API response."""


class ConnectionError(Exception):
    """Error to indicate there is an error in connection."""


class DeviceUnavailable(Exception):
    """Error to indicate device is not responding."""
