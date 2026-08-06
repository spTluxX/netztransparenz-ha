"""Thin async client for the Netztransparenz WebAPI (market values)."""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta

import aiohttp

from .const import (
    API_BASE,
    DATA_PATH,
    METRIC_SOLAR,
    METRIC_SPOT,
    METRIC_WIND_OFFSHORE,
    METRIC_WIND_ONSHORE,
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class NtAuthError(Exception):
    """Raised when credentials are rejected by the identity service."""


class NtApiError(Exception):
    """Raised for connectivity or unexpected API errors."""


async def async_get_token(
    session: aiohttp.ClientSession, client_id: str, client_secret: str
) -> str:
    """Exchange client credentials for a bearer token (valid ~1h)."""
    try:
        async with session.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status in (400, 401):
                raise NtAuthError(f"Auth rejected (HTTP {resp.status})")
            resp.raise_for_status()
            payload = await resp.json()
    except aiohttp.ClientError as err:
        raise NtApiError(f"Token request failed: {err}") from err

    token = payload.get("access_token")
    if not token:
        raise NtApiError("No access_token in token response")
    return token


async def async_fetch_marketpremium(
    session: aiohttp.ClientSession, token: str, days_back: int = 120
) -> str:
    """Fetch the market-value CSV.

    Per the official endpoint list, 'data/marketpremium' takes NO date range,
    so we call it plain first. A dated variant is tried as a fallback in case
    the route ever changes.
    """
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/plain"}
    end = datetime.now()
    start = end - timedelta(days=days_back)
    fmt = "%Y-%m-%dT%H:%M:%S"
    candidates = [
        f"{API_BASE}/{DATA_PATH}",
        f"{API_BASE}/{DATA_PATH}/{start.strftime(fmt)}/{end.strftime(fmt)}",
    ]

    last_status: int | None = None
    for url in candidates:
        try:
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status in (401, 403):
                    raise NtAuthError(
                        f"Token not accepted for data (HTTP {resp.status})"
                    )
                if resp.status == 404:
                    last_status = 404
                    continue
                resp.raise_for_status()
                text = await resp.text()
                if text.strip():
                    return text
                last_status = resp.status
        except aiohttp.ClientResponseError as err:
            last_status = err.status
            continue
        except aiohttp.ClientError as err:
            raise NtApiError(f"Data request failed: {err}") from err

    raise NtApiError(
        f"No market-value data returned from the API (last HTTP {last_status})"
    )


def _to_float(raw: str) -> float | None:
    """Parse a German-formatted number ('5,455' or '1.234,56') to float."""
    s = raw.strip()
    if not s:
        return None
    if "," in s and "." in s:  # dot = thousands separator
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _match_column(header: list[str]) -> dict[str, int]:
    """Map metric keys to column indices by header keywords (layout-agnostic)."""
    idx: dict[str, int] = {}
    for i, cell in enumerate(header):
        h = cell.lower()
        if "solar" in h and "wind" not in h and METRIC_SOLAR not in idx:
            idx[METRIC_SOLAR] = i
        elif "wind" in h and ("land" in h or "onshore" in h):
            idx[METRIC_WIND_ONSHORE] = i
        elif "wind" in h and ("see" in h or "offshore" in h):
            idx[METRIC_WIND_OFFSHORE] = i
        elif "spot" in h and METRIC_SPOT not in idx:
            idx[METRIC_SPOT] = i
    return idx


def _find_date_column(header: list[str]) -> int:
    for i, cell in enumerate(header):
        h = cell.lower()
        if "datum" in h or "monat" in h or "date" in h or "zeit" in h:
            return i
    return 0


def parse_marketpremium(csv_text: str) -> dict:
    """Return the most recent monthly values (ct/kWh) plus the period label.

    Result: {"solar": float|None, "wind_onshore": ..., "wind_offshore": ...,
             "spotmarktpreis": ..., "period": str|None}
    """
    reader = csv.reader(io.StringIO(csv_text), delimiter=";")
    rows = [r for r in reader if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise NtApiError("Empty or malformed market-value CSV")

    header = rows[0]
    cols = _match_column(header)
    if METRIC_SOLAR not in cols:
        raise NtApiError(f"Could not locate Solar column. Header: {header}")
    date_col = _find_date_column(header)

    # Walk rows from newest (bottom) to oldest; take the first with a Solar value.
    for row in reversed(rows[1:]):
        solar_idx = cols[METRIC_SOLAR]
        if len(row) <= solar_idx:
            continue
        solar_val = _to_float(row[solar_idx])
        if solar_val is None:
            continue
        result: dict = {"period": row[date_col].strip() if len(row) > date_col else None}
        for metric, i in cols.items():
            result[metric] = _to_float(row[i]) if len(row) > i else None
        return result

    raise NtApiError("No dated row with a numeric Solar value found")
