# Agent Design

Design notes for the weather-traffic-analyst — the AI report generator at the core of the application.

## Purpose

Translate a structured snapshot of weather and traffic data into a short, operational text report for fleet operators and dispatchers. The report should help the reader make a decision in the next 30 minutes — not write a research paper.

## Output shape

A Report object containing:

- generated_at, model, confidence
- language ("no" or "en")
- summary (1-2 sentence headline)
- sections (ordered paragraphs: situation, impact, recommendations, outlook)
- sources (list of cited data sources)
- referenced_entities (road/tunnel/bridge names — used by the frontend for highlighting)

## Prompt structure

- **System prompt:** defines the analyst persona, the output contract, and the writing style (operational, concrete, action-oriented, honest about uncertainty).
- **User message:** delivers a compact JSON snapshot of the latest data: current weather, recent precipitation, active incidents, closed tunnels, and a short historical baseline.

## Versioning

Prompt versions live under backend/app/agent/prompts/ as v1.py, v2.py, etc. Active version selected via configuration. Diffs between versions are documented in this file.

### v1 — initial

**Model:** `claude-sonnet-4-6` (verified against Anthropic docs 2026-05-03).
Pinned as `CLAUDE_MODEL` constant in `backend/app/agent/claude_client.py`.

**Output contract:** The model is instructed to return a single JSON object matching
the `Report` schema (defined in `backend/app/agent/models.py`). The object includes:
`confidence` (float 0–1), `language`, `summary` (1–2 sentence headline), `sections`
(four ordered entries: situation / impact / recommendations / outlook), `sources`,
and `referenced_entities` (road/tunnel/bridge names for frontend highlighting).
No prose, no markdown fences — raw JSON only.

**Prompt structure:**
- *System turn* (`SYSTEM_PROMPT_V1` in `backend/app/agent/prompts.py`): defines the
  analyst persona, the exact JSON schema required, per-section content expectations,
  writing style rules (concrete entities, numbers with units, no vague hedges), the
  language rule (Norwegian incident descriptions must not be translated), and a
  confidence calibration table (freshness of data → expected confidence range).
- *User turn* (`build_user_message()`): compact JSON snapshot containing
  `request.language`, `request.region`, `weather` (all non-None WeatherSnapshot
  fields), `active_incidents` (list of non-None TrafficIncident fields), and
  `incident_count`. None values are stripped to save tokens. A `weather_note` or
  `incidents_note` is added when data is absent.

**Safety / correctness rules enforced in the prompt:**
1. Never fabricate measurements not present in the input — say "not reported" instead.
2. If weather data is > 90 min old, flag it in the situation section and lower confidence.
3. Confidence reflects data quality, not severity — a well-documented storm gets a high score.
4. Norwegian incident descriptions (`description` field from Vegvesen) are quoted verbatim
   or paraphrased with an explicit signal; never silently translated.
5. Recommendations use imperative sentences; vague phrases like "exercise caution" are
   disallowed unless paired with a concrete action.

**Degraded mode:** If the DB read, Claude API call, or JSON parse fails, `generate_report()`
returns a `Report` with `confidence=0.0`, an empty `sections` list, and a `sources` entry
that names the failure reason. The API endpoint returns HTTP 200 with this degraded report
rather than 503, so the frontend always receives a structured object it can render.

## Failure modes seen so far

- **DetachedInstanceError in seed_demo.py:** SQLModel objects accessed after session close
  during summary computation. Fixed by extracting primitive dicts inside the session block.
- **JSON parse failure (anticipated):** Claude may occasionally wrap output in markdown
  code fences despite explicit instructions. `_extract_json()` in `analyst.py` strips
  fences and falls back to regex extraction before raising.

## Evaluation

Manual review of generated reports against the actual situation. A small fixture set of historical snapshots will be used to regression-test prompt changes.

## See also

- .claude/agents/weather-traffic-analyst.md — operational rules for the sub-agent
- docs/AI_WORKFLOW.md — broader AI usage in the project
