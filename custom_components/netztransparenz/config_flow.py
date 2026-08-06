"""Config and options flow for Netztransparenz Marktwerte."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import NtApiError, NtAuthError, async_get_token
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PRICE_SOURCE,
    CONF_PRICE_UNIT,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_PRICE_UNIT,
    DOMAIN,
    METRICS,
    UNIT_CT,
    UNIT_EUR,
)

_SOURCE_OPTIONS = [
    SelectOptionDict(value=key, label=meta["name"]) for key, meta in METRICS.items()
]
_UNIT_OPTIONS = [
    SelectOptionDict(value=UNIT_EUR, label="Euro per kWh (\u20ac/kWh)"),
    SelectOptionDict(value=UNIT_CT, label="Cent per kWh (ct/kWh)"),
]


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_PRICE_SOURCE,
                default=defaults.get(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_SOURCE_OPTIONS, mode=SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Required(
                CONF_PRICE_UNIT,
                default=defaults.get(CONF_PRICE_UNIT, DEFAULT_PRICE_UNIT),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_UNIT_OPTIONS, mode=SelectSelectorMode.DROPDOWN
                )
            ),
        }
    )


class NetztransparenzConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial UI setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                await async_get_token(
                    session,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                )
            except NtAuthError:
                errors["base"] = "invalid_auth"
            except NtApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_CLIENT_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Netztransparenz Marktwerte",
                    data={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                    },
                    options={
                        CONF_PRICE_SOURCE: user_input[CONF_PRICE_SOURCE],
                        CONF_PRICE_UNIT: user_input[CONF_PRICE_UNIT],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Required(
                    CONF_PRICE_SOURCE, default=DEFAULT_PRICE_SOURCE
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=_SOURCE_OPTIONS, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(
                    CONF_PRICE_UNIT, default=DEFAULT_PRICE_UNIT
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=_UNIT_OPTIONS, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return NetztransparenzOptionsFlow()


class NetztransparenzOptionsFlow(OptionsFlow):
    """Let the user change the price source / unit after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self.config_entry.options)),
        )
