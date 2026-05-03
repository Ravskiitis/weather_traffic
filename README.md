# weather_traffic

**AI-powered operational dashboard for weather and traffic intelligence in the Bergen region.**

![Status: MVP](https://img.shields.io/badge/status-MVP-orange)
![Built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-blueviolet)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

Fleet operators, construction site managers, and infrastructure dispatchers in Bergen deal with the same problem every shift: weather and traffic data live in separate systems, and synthesising them into a routing decision takes time they don't have. **weather_traffic** pulls live weather from MET Norway and traffic incidents from Statens vegvesen, stores both in a time-series database, and feeds them to a Claude-powered AI analyst that produces a 30-second operational briefing — in Norwegian or English, with a calibrated confidence score.

> [Screenshot of dashboard goes here — docs/screenshots/dashboard.png]

**Live demo:** [URL pending — Render deployment in progress]  
The dashboard requires the backend. See [Setup](#setup) below.

---

## What it does

- **Live weather** — MET Norway Locationforecast 2.0, Bergen sentrum (60.39°N, 5.32°E), updated periodically
- **Traffic incidents** — Statens vegvesen Datex II integration is implemented and awaits production credentials; the dashboard currently runs on realistic Bergen demo data (E39, E16, Fv585, major tunnels)
- **AI operational reports** — `POST /api/agent/report` calls Claude Sonnet 4.6 with a structured prompt; response includes summary, four ordered sections (situation / impact / recommendations / outlook), confidence score (0–1), and cited sources
- **Print-to-PDF export** — `window.print()` with a dedicated `@media print` layout that isolates the AI card, adds a page header/footer, and suppresses the map, charts, and nav
- **Bilingual UI** — Norwegian Bokmål / English toggle, persisted in `localStorage`, all strings in `src/i18n/en.json` and `no.json`
- **Leaflet map** — Bergen region, zoom 10, incident markers colour-coded by severity (high: orange, medium: amber, low: green)
- **7-day correlation chart** — Recharts ComposedChart overlaying incident counts against wind speed and precipitation (mock data; historical collection is on the v2 roadmap)

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLModel (SQLite), httpx, python-dotenv |
| AI | Anthropic SDK — Claude Sonnet 4.6 (`claude-sonnet-4-6`) |
| Frontend | Astro 4, React islands, Tailwind CSS, TypeScript |
| Charts / Map | Recharts, Leaflet + react-leaflet, Lucide icons |
| Dev tooling | Claude Code + three sub-agents, Ruff, Prettier |
| Infrastructure | Planned: Docker Compose on Render |

---

## Architecture

```
MET Norway API ──────────────────────────────────────┐
                                                      ▼
Statens vegvesen Datex II ──► FastAPI backend ──► SQLite DB
                               (app/data/)       (app/db/)
                                    │
                                    ▼
                          AI analyst (app/agent/)
                          ┌──────────────────────┐
                          │ 1. read latest data   │
                          │ 2. build prompt       │──► Claude API
                          │ 3. parse JSON report  │◄── structured JSON
                          └──────────────────────┘
                                    │
                                    ▼
                          Astro frontend ──► Browser
                          (islands: React)
```

**Request flow for "Generate AI report":**
1. Dashboard calls `POST /api/agent/report?language=no`
2. `analyst.py` reads the latest `WeatherSnapshot` and all active/monitored `TrafficIncident` rows
3. `build_user_message()` strips `None` fields and serialises to compact JSON
4. `call_model()` sends system prompt + user message to Claude Sonnet 4.6 (`max_tokens=4096`)
5. `_extract_json()` parses the response (with fence-stripping fallback)
6. A `Report` pydantic object is validated and cached for 15 minutes
7. Frontend receives the report, extracts top-3 actions and key risks, and renders the card

---

## The AI agent

The `weather-traffic-analyst` agent lives in `backend/app/agent/`. It takes a snapshot of the current weather and active incidents and returns a fully structured `Report` object — no free-form text, no markdown, raw JSON matching the pydantic schema.

**Prompt design choices worth noting** (`backend/app/agent/prompts.py` — readable as a deliverable in itself):

- **Confidence calibration** is explicit in the prompt, not inferred:

  | Range | Meaning |
  |---|---|
  | 0.85 – 1.00 | Fresh data < 30 min, clear situation, multiple sources |
  | 0.60 – 0.84 | Data 30–90 min old, or ambiguous / single-source |
  | 0.30 – 0.59 | Stale > 90 min, conflicting signals, or data gaps |
  | < 0.30 | Severely degraded — summary must open with an uncertainty warning |

- **No-hallucination rule:** if a measurement is not in the input, the model must write "not reported" — never guess
- **No-translation rule:** Norwegian incident descriptions from Vegvesen are quoted verbatim or paraphrased with an explicit signal; never silently translated
- **Recommendations must be imperative and specific:** "reduce speed to 50 km/h on Rv555 approaching Fløyfjelltunnelen" is valid; "exercise caution" alone is not
- **Degraded mode:** if the DB read, API call, or JSON parse fails, the endpoint returns HTTP 200 with `confidence=0.0` and a structured error report — the frontend never receives an unhandled exception

> [Screenshot of generated report goes here — docs/screenshots/ai-report.png]

---

## Data sources and current limitations

| Data | Status | Notes |
|---|---|---|
| Weather (MET Norway) | ✅ Live | CC BY 4.0. Bergen sentrum. No API key required. |
| Traffic incidents (Vegvesen) | ⏳ Pending credentials | Integration built and tested with seed data. Awaiting approval from Statens vegvesen. |
| 7-day correlation chart | 🟡 Mock | Clearly labeled in the UI ("Demodata — historisk API venter"). Requires scheduled history collection (v2). |
| Precipitation tile | ℹ️ Rate, not total | Displays `precipitation_mm_h` — current hourly rate from MET Norway, not a 24-hour accumulation. |
| Weather forecast bars | 🔲 Not yet | Prototype design included 24h forecast sparklines and weather symbol icons; requires a forecast endpoint (v2). |
| History / Reports / Settings tabs | 🔲 Scaffolded | Navigation tabs exist; data layers not yet built. |

---

## Roadmap

### v2 — Route-aware proactive alerts
A second AI agent (`route-advisor`) monitors planned fleet routes against active incidents and pushes targeted alerts to dispatchers when a route is affected.

```
Route input → APScheduler (poll every 5 min) → route-advisor agent
  → short alert JSON → email / SMS / Slack delivery
```

### v2 — Additional
- Forecast endpoint → weather card forecast bars and richer KPI tiles
- Persistent report storage → Reports tab with date filtering
- Real-time push (SSE or WebSocket) instead of manual refresh
- APScheduler-driven historical weather collection → real Pearson correlation analysis replacing mock chart data

---

## Setup

**Prerequisites:** Python 3.11+, Node.js 20+, npm, an Anthropic API key ([console.anthropic.com](https://console.anthropic.com/))

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp ../.env.example .env
# Edit .env — set ANTHROPIC_API_KEY at minimum

python scripts/seed_demo.py          # loads 8 realistic Bergen demo incidents
uvicorn app.main:app --reload        # → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
echo 'PUBLIC_BACKEND_URL=http://localhost:8000' > .env
npm run dev                          # → http://localhost:4321
```

Open **http://localhost:4321**. Click **"Generate fresh AI report"** to invoke Claude.

> **Cost:** one report generation ≈ $0.03 in API credits. Free tier works.

---

## Project structure

```
weather_traffic/
├── backend/
│   ├── app/
│   │   ├── agent/          AI analyst — models, prompt (prompts.py), Claude client
│   │   ├── api/            FastAPI routers — weather, traffic, agent
│   │   ├── core/           Settings via pydantic-settings + .env
│   │   ├── data/           MET Norway + Vegvesen fetchers (httpx, Datex II XML)
│   │   └── db/             SQLModel schema, session, repositories
│   └── scripts/
│       └── seed_demo.py    8 realistic Bergen incidents for development
├── frontend/
│   └── src/
│       ├── islands/        React islands — Dashboard, map, charts, AI card
│       ├── components/     Static Astro components (Nav)
│       ├── i18n/           en.json / no.json — all UI strings
│       └── lib/api.ts      Typed fetch client for the backend
├── docs/
│   ├── ARCHITECTURE.md
│   ├── agent-design.md     Prompt design decisions and failure log
│   └── design/             Claude Design prototype (immutable reference)
└── .claude/agents/         Sub-agent definitions (data-collector, analyst, frontend)
```

---

## AI workflow

This project was built with **Claude Code** as the primary development tool, using three specialised sub-agents defined in `.claude/agents/` — each owning its domain: data collection, AI agent design, and frontend implementation. Backend, frontend, database schema, prompt engineering, and print CSS were written in a single continuous session of approximately 4 hours from an empty repository to a running MVP.

See [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md) for the full session log, including prompts that worked, prompts that failed, and lessons learned.

---

Weather data: [MET Norway](https://api.met.no/) (CC BY 4.0) · Traffic data: [Statens vegvesen / NPRA](https://www.vegvesen.no/en/fag/technology/open-data/) (NLOD / CC BY 4.0)

Built by [Rafał](https://github.com/Ravskiitis)
