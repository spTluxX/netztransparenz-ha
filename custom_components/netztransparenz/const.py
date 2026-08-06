"""Constants for the Netztransparenz Marktwerte integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "netztransparenz"
PLATFORMS = [Platform.SENSOR]

# --- Config / options keys -------------------------------------------------
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_PRICE_SOURCE = "price_source"
CONF_PRICE_UNIT = "price_unit"

# --- API -------------------------------------------------------------------
TOKEN_URL = "https://identity.netztransparenz.de/users/connect/token"
API_BASE = "https://ds.netztransparenz.de/api/v1"
# Monthly EEG market values (Monatsmarktwerte) -> API "Format 12".
DATA_PATH = "data/marktpraemie"

DEFAULT_SCAN_INTERVAL = timedelta(hours=12)

# --- Metrics ---------------------------------------------------------------
METRIC_SOLAR = "solar"
METRIC_WIND_ONSHORE = "wind_onshore"
METRIC_WIND_OFFSHORE = "wind_offshore"
METRIC_SPOT = "spotmarktpreis"

# Ordered so the config dropdown reads sensibly. Each entry: label + icon.
METRICS: dict[str, dict[str, str]] = {
    METRIC_SOLAR: {"name": "Marktwert Solar", "icon": "mdi:solar-power"},
    METRIC_WIND_ONSHORE: {"name": "Marktwert Wind Onshore", "icon": "mdi:wind-turbine"},
    METRIC_WIND_OFFSHORE: {"name": "Marktwert Wind Offshore", "icon": "mdi:wind-turbine"},
    METRIC_SPOT: {"name": "Marktwert EPEX (Spot)", "icon": "mdi:transmission-tower"},
}

# --- Units -----------------------------------------------------------------
UNIT_CT = "ct/kWh"
UNIT_EUR = "\u20ac/kWh"  # €/kWh

DEFAULT_PRICE_SOURCE = METRIC_SOLAR
DEFAULT_PRICE_UNIT = UNIT_EUR
