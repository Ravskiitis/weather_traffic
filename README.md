# weather_traffic

Analysis of weather impact on road traffic in Bergen, Norway, with an AI agent generating operational reports.

> **Status:** work in progress. Backend skeleton, configuration, and database schema are in place. Data fetchers, AI agent, frontend, and deployment are next.

## What this is

A B2B operational dashboard that pulls public Norwegian data — weather from MET Norway, traffic incidents from Statens vegvesen — stores time-series snapshots, and uses Anthropic's Claude API to generate short, action-oriented reports correlating weather conditions with road disruptions. Target audience: fleet operators, construction site managers, and infrastructure dispatchers.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLModel, SQLite, httpx, APScheduler, Anthropic SDK
- **Frontend:** Astro, React islands, Tailwind, Leaflet, Recharts (planned)
- **AI:** Anthropic Claude (Sonnet)
- **Build approach:** AI-driven development with Claude Code, structured via per-project sub-agents

## Repository layout

- .claude/agents/ — sub-agent definitions for Claude Code
- backend/ — FastAPI app, database, AI agent
- frontend/ — Astro app (planned)
- docs/ — architecture, API sources, AI workflow, design assets
- CLAUDE.md — project context for Claude Code

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system overview and key technical decisions
- [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md) — how AI tools are used in development
- [docs/api-sources.md](docs/api-sources.md) — external API references
- [docs/agent-design.md](docs/agent-design.md) — AI report generator design
- [docs/design/DESIGN.md](docs/design/DESIGN.md) — UI design source of truth

## Running the backend locally

See [backend/README.md](backend/README.md).

## Roadmap

- [x] Project foundation, sub-agents, design handoff
- [x] Backend skeleton, configuration, health endpoint
- [x] Database schema (weather snapshots, traffic incidents, links)
- [ ] MET Norway weather fetcher
- [ ] Statens vegvesen traffic fetcher
- [ ] AI report generator (Claude API)
- [ ] Astro frontend with bilingual UI
- [ ] Docker Compose deployment
- [ ] Live demo
