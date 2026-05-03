# CLAUDE.md — Project Context for Claude Code

This file is automatically read by Claude Code when working in this repository. It defines the project's purpose, stack, conventions, and constraints. Read it fully before making changes.

---

## Project: weather_traffic

**One-liner:** A B2B dashboard analyzing the impact of weather on road traffic in Bergen, Norway, with an AI agent that generates operational reports.

**Domain:** Road infrastructure operations, fleet logistics, and weather risk for the Bergen metropolitan area. The dashboard targets fleet operators, construction site managers, and infrastructure dispatchers who need a single view of current road conditions with AI-assisted interpretation.

---

## What the application does

1. **Pulls public Norwegian data:**
   - Weather: MET Norway Locationforecast 2.0 API (no key, User-Agent required)
   - Traffic: Statens vegvesen Datex II + Trafikkdata GraphQL (no key)
2. **Stores time-series snapshots** in SQLite for historical correlation.
3. **Generates AI analysis reports** using Anthropic's Claude API. The agent reads the latest data and produces an operational text report (rainfall vs incidents, tunnel closures, recommendations for fleet operators).
4. **Presents everything** as a B2B dashboard with KPI tiles, current weather, an interactive map, a 7-day correlation chart, and an active incidents table.

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLite, `anthropic` SDK, `httpx` for outbound HTTP, APScheduler for periodic data fetching.
- **Frontend:** Astro (with React islands where interactivity is needed), Tailwind CSS, Leaflet for maps, Recharts for charts. Bilingual UI (Norwegian Bokmål + English) with a toggle.
- **AI:** Anthropic Claude API. Use the latest available Claude Sonnet model — verify the exact model identifier from current Anthropic API docs at the time of implementation. Do not hardcode an outdated model ID.
- **Deployment target:** Eventually Docker Compose. Initially run directly on Raspberry Pi for fast iteration.

---

## Repository Layout (monorepo)

\`\`\`
weather_traffic/
├── backend/                FastAPI app, agent code, data fetchers, DB
├── frontend/               Astro app, dashboard UI
├── docs/                   Architecture, API sources, AI workflow, design assets
├── .claude/agents/         Sub-agent definitions (data-collector, analyst, frontend)
├── CLAUDE.md               This file
├── .env.example            Template for environment variables
└── .gitignore
\`\`\`

---

## Conventions

### General
- **Language of code, comments, commits, docs:** English.
- **Language of UI:** Norwegian (bokmål) and English, switchable. All user-facing strings live in i18n files, never hardcoded in components.
- **Commits:** Conventional Commits (\`feat:\`, \`fix:\`, \`docs:\`, \`chore:\`, \`refactor:\`). One logical change per commit.
- **No secrets in code, ever.** All keys via environment variables loaded from \`.env\`.
- **Vegvesen Datex II:** Requires HTTP Basic Auth (`VEGVESEN_USERNAME` / `VEGVESEN_PASSWORD`); incident descriptions must be displayed in Norwegian as-is (no translation); any UI showing this data must display "Statens vegvesen / NPRA" as the data source.

### Python (backend)
- Format with \`ruff format\`. Lint with \`ruff check\`.
- Type hints on all public functions.
- Use \`pydantic\` models for API request/response shapes and for parsing external API payloads.
- Async by default (FastAPI + httpx async).
- Folder layout: \`backend/app/{api,agent,data,models,db,core}\`.

### Astro/TypeScript (frontend)
- Format with Prettier. Lint with ESLint.
- Tailwind utility classes; no inline styles unless absolutely needed.
- React islands only where interactivity is required (charts, map, language toggle). Static content stays as \`.astro\` components.
- Design tokens (colors, spacing, fonts) live in \`tailwind.config.mjs\` and match the Claude Design prototype in \`docs/design/raw/prototype.html\`.

### Documentation
- Every non-trivial design decision goes into \`docs/ARCHITECTURE.md\` or a focused doc under \`docs/\`.
- \`docs/AI_WORKFLOW.md\` is a living document — append notes about how AI was used, prompts that worked, prompts that failed, and lessons learned.

---

## What to DO

- Default to **paraphrasing the design**, not pixel-perfect cloning. The prototype in \`docs/design/raw/prototype.html\` is the source of truth for layout and styling intent — match it functionally and visually, but write idiomatic Astro/Tailwind, not raw HTML copies.
- **Validate external API responses** with pydantic. Never trust shape; APIs change.
- **Cache external API calls** sensibly (e.g., 5–10 minute TTL for weather, 1–2 minutes for traffic) — be a good citizen on free public APIs.
- Write **small, testable functions**. Prefer pure functions for data transformations.
- For every new feature, update relevant docs (\`docs/\`) in the same commit.

## What to NOT DO

- Do not hardcode API keys, model identifiers, or environment-specific URLs.
- Do not commit \`.env\`, the SQLite database, or anything in \`backend/data/\`.
- Do not introduce heavy dependencies without justifying them in the commit message.
- Do not generate fake or illustrative data into the production database — use a separate \`backend/scripts/seed_demo.py\` for any demo data, and document it.
- Do not silently swallow exceptions from external APIs — log them and degrade gracefully.
- Do not modify files in \`docs/design/raw/\` — those are immutable design artifacts from Claude Design.

---

## Sub-agents

This repository defines specialized sub-agents in \`.claude/agents/\`. Use them for delegated work:

- **data-collector** — fetches and persists data from MET Norway and Statens vegvesen.
- **weather-traffic-analyst** — the AI report generator; designs prompts and orchestrates Claude API calls.
- **astro-frontend** — implements UI components based on the Claude Design prototype.

When a task fits one of these roles, delegate to the corresponding sub-agent rather than doing it inline.

---

## AI Workflow note

This project is being built with Claude Code as the primary coding partner, with Claude Design used for the UI prototype. The development process itself is part of the deliverable — the contents of \`docs/AI_WORKFLOW.md\` should reflect real prompts, real iterations, and real lessons. Honesty over polish.
