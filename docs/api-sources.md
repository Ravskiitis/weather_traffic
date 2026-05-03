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
- **Notes:** to be filled in by data-collector as findings emerge.

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
