# Netztransparenz Marktwerte — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/spTluxX/netztransparenz-ha/actions/workflows/validate.yml/badge.svg)](https://github.com/spTluxX/netztransparenz-ha/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Pulls the official **monthly EEG market values** (Monatsmarktwerte) published by the German transmission system operators on [netztransparenz.de](https://www.netztransparenz.de) into Home Assistant, and exposes a ready-to-use **price sensor** you can drop straight into the Energy dashboard as your feed-in (or reference) price.

The values come from the official [Netztransparenz WebAPI](https://api-portal.netztransparenz.de/) (`marketpremium` dataset) — no scraping, no screen-parsing.

## What you get

Five sensors, updated automatically (the TSOs publish new values by the 10th working day of each month):

| Sensor | Description | Unit |
| --- | --- | --- |
| `sensor.marktwert_solar` | Monatsmarktwert Solar (MW Solar) | ct/kWh |
| `sensor.marktwert_wind_onshore` | Monatsmarktwert Wind an Land | ct/kWh |
| `sensor.marktwert_wind_offshore` | Monatsmarktwert Wind auf See | ct/kWh |
| `sensor.spotmarktpreis` | Durchschnittlicher Spotmarktpreis | ct/kWh |
| `sensor.netztransparenz_marktwerte_price` | **The value you selected**, converted to your chosen unit | €/kWh or ct/kWh |

Each sensor carries the `period` it applies to (e.g. `März 2026`) as an attribute.

The **Price** sensor is the one to use as your Energy-dashboard price. In the integration options you pick:

- **Price source** — a dropdown: Marktwert Solar / Wind Onshore / Wind Offshore / Spotmarktpreis
- **Price unit** — €/kWh (default, what the Energy dashboard expects) or ct/kWh

## Prerequisites: API credentials

The WebAPI is free but requires OAuth2 credentials:

1. Register at the [Netztransparenz Extranet](https://extranet.netztransparenz.de).
2. Open the **OAuth Manager** and **create a client** (up to 5 per account).
3. Copy the **Client-ID** and **Client-Secret** (the secret is shown only once).

## Installation (HACS)

1. HACS → three-dot menu → **Custom repositories**.
2. Add `https://github.com/spTluxX/netztransparenz-ha` with category **Integration**.
3. Install **Netztransparenz Marktwerte**, then restart Home Assistant.
4. Settings → **Devices & Services** → **Add Integration** → *Netztransparenz Marktwerte*.
5. Paste your Client-ID / Client-Secret, choose the price source and unit.

To change the price source or unit later: the integration's **Configure** button.

## Manual installation

Copy `custom_components/netztransparenz/` into your HA `config/custom_components/` folder and restart.

## Use it in the Energy dashboard

Settings → Dashboards → **Energy** → Grid consumption / Return to grid → *Use an entity with current price* → select `sensor.netztransparenz_marktwerte_price`.

Tip: many feed-in contracts pay a percentage of MW Solar. If you want, create a Template sensor that multiplies the Price sensor by your factor and use that instead.

## How it works

- OAuth2 `client_credentials` → bearer token (`identity.netztransparenz.de`).
- `GET /api/v1/data/marketpremium/{from}/{to}` → CSV (semicolon, German decimals).
- The parser locates columns by header keywords (Solar / Wind / Spot), so it is resilient to column-order changes, and takes the most recently published month.
- Polls every 12 hours (the data only changes monthly, so this simply catches the publication promptly).

## Troubleshooting

- **"invalid_auth"** — check the Client-ID/Secret; regenerate the secret in the Extranet if unsure.
- **Sensors `unknown` right after setup** — the current month may not be published yet; the integration serves the latest available month. Values appear once the TSOs publish.
- Enable debug logging:
  ```yaml
  logger:
    logs:
      custom_components.netztransparenz: debug
  ```

## Data source & attribution

Market values are published by the four German TSOs (50Hertz, Amprion, TenneT, TransnetBW) on netztransparenz.de and retrieved via their official WebAPI. This integration is an independent community project and is **not** affiliated with or endorsed by netztransparenz.de or the TSOs.

## License

[MIT](LICENSE) © spTluxX
