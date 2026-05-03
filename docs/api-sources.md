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
- **Auth:** HTTP Basic Auth. Registration is required and free of charge. Register at: https://www.vegvesen.no/en/fag/technology/open-data/a-selection-of-open-data/what-is-datex/get-access/ — credentials go in `VEGVESEN_USERNAME` / `VEGVESEN_PASSWORD` in `.env`. Note: initial implementation assumed this endpoint was open; the auth requirement was discovered at integration time.
- **License:** Norwegian Licence for Open Government Data (NLOD) / CC BY 4.0
- **Terms of use:** Do not translate Norwegian incident descriptions — display them as-is. Credentials must remain server-side; never expose them to the browser or include them in frontend bundles. Any UI displaying this data must attribute the source as "Statens vegvesen / NPRA".
- **Used for:** Active traffic situations, incidents, road closures, tunnel status in the Bergen area.
- **Endpoint used:** `https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/GetSituation/pullsnapshotdata`
  - TODO: Verify this URL against the Vegvesen ATLAS developer portal. The pattern matches the Datex II v3.1 pull-snapshot model but has not been confirmed against a live response. Fallback candidates: `/datexapi/SituationPublication/pullsnapshotdata`, `/datexapi/situation`.
- **Response format:** XML (Datex II v3).
- **Feed scope:** National (all of Norway). Filtered client-side to Bergen bounding box (lat 60.2–60.6, lon 4.9–5.7). Records without coordinates are skipped.
- **XML parsing approach:** Namespace-agnostic using local tag names. This is intentional — the exact namespace URI in Vegvesen's Datex II dialect has not been confirmed.
  - TODO: On first successful fetch, log `root.tag` to confirm the namespace and element structure. Update `_extract_raw()` in `backend/app/data/vegvesen.py` with confirmed element paths.
- **Key element paths (unconfirmed — verify against live response):**
  - Situation ID: `<situation id="...">` attribute
  - Record type: `<situationRecord xsi:type="Accident|Roadworks|...">` attribute
  - Coordinates: `<latitude>` / `<longitude>` somewhere under `<locationForDisplay>` or `<pointCoordinates>`
  - Timestamps: `<startTime>` / `<endTime>` under `<situationRecord>`
  - Severity: `<overallSeverity>` under `<situation>`
- **Incident type mapping:** substring-matched from xsi:type. Tunnel closures may come as a Vegvesen extension type — revisit once real types are seen.
- **Datetime note:** Datetimes are ISO 8601 with timezone. Strip tzinfo before persisting (naive UTC, same convention as MET Norway).

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
