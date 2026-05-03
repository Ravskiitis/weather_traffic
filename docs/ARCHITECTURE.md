# Architecture

High-level technical overview of the weather_traffic application.

## Status

Living document. Updated as the architecture evolves.

## System overview

Three layers:

1. **Data ingestion** (backend/app/data) — periodic fetchers pull weather and traffic data from Norwegian public APIs and persist time-series snapshots to SQLite.
2. **AI analyst** (backend/app/agent) — on demand or on a schedule, reads the latest snapshot from the database, calls the Anthropic Claude API, and produces a structured operational report.
3. **Web dashboard** (frontend/) — Astro app that consumes the backend's JSON API and renders KPI tiles, current weather, an interactive map, a 7-day correlation chart, an AI analysis card, and an active incidents table. Bilingual (Norwegian Bokmål + English).

## Data flow

External APIs → data-collector → SQLite → repositories → backend HTTP API → Astro frontend → user

For the AI analysis path:
SQLite → analyst (prompt builder) → Claude API → Report object → SQLite (cached) → backend HTTP API → frontend

## Key technical decisions

To be filled in as decisions are made and rationalised.

- **Monorepo with backend/ and frontend/** — single source of truth, single CI pipeline, simpler local development.
- **SQLite over Postgres** — sufficient for a single-region time-series workload at this scale; zero-ops; easy to ship.
- **Astro + React islands over a full SPA** — the dashboard is largely static; only charts, map, and toggle need interactivity.
- **No Docker initially** — fast iteration during development; containerisation deferred until the application stabilises.

## Open questions

- Caching strategy for AI reports (TTL? regenerate on every fetch?).
- Map provider (OpenStreetMap raster tiles vs vector tiles).
- Authentication (none for MVP; revisit if deploying publicly).

## See also

- docs/api-sources.md — external API details
- docs/agent-design.md — AI prompt design and evolution
- docs/AI_WORKFLOW.md — how AI tools are used in development
- docs/design/DESIGN.md — UI design source of truth
