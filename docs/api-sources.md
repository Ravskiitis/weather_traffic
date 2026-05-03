# API Sources

Reference for all external APIs consumed by the application.

## MET Norway — Locationforecast 2.0

- **Endpoint:** https://api.met.no/weatherapi/locationforecast/2.0/
- **Auth:** None
- **Required:** A descriptive User-Agent header. Requests without it are rate-limited or blocked. Configured via MET_USER_AGENT in .env.
- **Terms of service:** https://api.met.no/doc/TermsOfService
- **License:** Norwegian Licence for Open Government Data (NLOD), CC BY 4.0
- **Rate limits:** Be polite. Respect the Expires response header — do not poll faster than that. Cache aggressively.
- **Used for:** Current weather and short-term forecast at Bergen sentrum (Florida weather station coordinates).
- **Endpoint (with params):** `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.39&lon=5.32`
- **Payload paths used:**
  - `properties.meta.updated_at` → snapshot `timestamp` (ISO 8601, UTC/Z — strip tzinfo for SQLite)
  - `properties.timeseries[0].data.instant.details` → temperature, wind speed/direction, humidity, pressure
  - `properties.timeseries[0].data.next_1_hours.summary.symbol_code` → `weather_symbol` (e.g. `"heavyrain"`)
  - `properties.timeseries[0].data.next_1_hours.details.precipitation_amount` → `precipitation_mm_h`
- **Known gaps:** The compact endpoint does not include apparent temperature ("feels like"). `feels_like_c` is always `None` from this source. `next_1_hours` may be absent for the furthest-future timeseries entries; always check for None before accessing.
- **Datetime note:** All datetimes arrive timezone-aware (UTC, "Z" suffix). Strip tzinfo before persisting — SQLite stores naive UTC throughout this project.

## Statens vegvesen — Datex II

- **Endpoint:** https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/
- **Auth:** None for public endpoints.
- **License:** NLOD / CC BY 4.0
- **Used for:** Active traffic situations, incidents, road closures, tunnel status in the Bergen area.
- **Notes:** to be filled in.

## Statens vegvesen — Trafikkdata GraphQL

- **Endpoint:** https://trafikkdata-api.atlas.vegvesen.no/
- **Auth:** None
- **Used for:** Traffic flow measurements at fixed sensors where relevant for correlation analysis.
- **Notes:** to be filled in.

## Anthropic Claude API

- **Endpoint:** https://api.anthropic.com/v1/messages
- **Auth:** Bearer token via ANTHROPIC_API_KEY environment variable.
- **Model:** Latest available Claude Sonnet at the time of implementation. Verified against current Anthropic API docs — not hardcoded to a stale ID.
- **Used for:** AI report generation in the weather-traffic-analyst sub-agent.

## See also

- docs/agent-design.md — how the Claude API is used
- docs/ARCHITECTURE.md — where each API fits in the system
