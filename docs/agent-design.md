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

To be written.

## Failure modes seen so far

To be appended.

## Evaluation

Manual review of generated reports against the actual situation. A small fixture set of historical snapshots will be used to regression-test prompt changes.

## See also

- .claude/agents/weather-traffic-analyst.md — operational rules for the sub-agent
- docs/AI_WORKFLOW.md — broader AI usage in the project
