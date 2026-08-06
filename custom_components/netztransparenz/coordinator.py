"""DataUpdateCoordinator for Netztransparenz market values."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    NtApiError,
    NtAuthError,
    async_fetch_marketpremium,
    async_get_token,
    parse_marketpremium,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NetztransparenzCoordinator(DataUpdateCoordinator[dict]):
    """Fetch and cache the latest monthly market values."""

    def __init__(
        self, hass: HomeAssistant, client_id: str, client_secret: str
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._client_id = client_id
        self._client_secret = client_secret

    async def _async_update_data(self) -> dict:
        session = async_get_clientsession(self.hass)
        try:
            token = await async_get_token(
                session, self._client_id, self._client_secret
            )
            csv_text = await async_fetch_marketpremium(session, token)
            return parse_marketpremium(csv_text)
        except NtAuthError as err:
            # Trigger HA's reauth flow instead of just failing.
            raise ConfigEntryAuthFailed(str(err)) from err
        except NtApiError as err:
            raise UpdateFailed(str(err)) from err
