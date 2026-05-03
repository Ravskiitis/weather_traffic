# AI Workflow

This is a living document describing how AI tools are used in the development of weather_traffic. It is intentionally honest — successes, failures, and lessons learned.

## Tools

- **Claude Code** (terminal-based agentic coding) — primary coding partner. Runs on a Raspberry Pi over SSH. Reads CLAUDE.md and .claude/agents/ for context.
- **Claude Design** (Anthropic Labs, Research Preview) — used to prototype the dashboard UI before any code was written. The exported design lives in docs/design/raw/ and is the source of truth for the visual implementation.
- **Claude (web app)** — used as a strategic and architectural sounding board: project planning, technology choices, prompt design, documentation review.

## Working principles

1. **Design before code.** UI was prototyped in Claude Design before any frontend file existed. This forced product thinking up front.
2. **Context before action.** CLAUDE.md and the three sub-agent definitions in .claude/agents/ were written before Claude Code touched a single line of application code. The cost is up-front; the payoff is consistency.
3. **Sub-agents have hard scope.** data-collector does not generate AI reports. weather-traffic-analyst does not fetch external APIs. astro-frontend does not call Claude. Clear ownership prevents code from drifting.
4. **Documentation in the same commit as the change.** Architecture decisions, API findings, and prompt evolutions are committed alongside the code that motivates them, not after.
5. **Honesty over polish.** This document records what actually happened, including dead ends and reverts. The goal is a credible workflow record, not a marketing brochure.

## Notable prompts and iterations

### Session 1 — 2026-05-03 — Foundation

**What was attempted:**
Bootstrapping the entire project from zero — repo connection, project context (CLAUDE.md), three sub-agent definitions, documentation skeleton, design handoff from Claude Design, backend skeleton (FastAPI + config + health endpoint), and the database schema.

**Approach:**
Strict separation between strategic conversation (Claude web) and execution (Claude Code on the Raspberry Pi). All structural files (CLAUDE.md, sub-agents, docs, .gitignore) were authored before any application code. Claude Code received the orientation prompt first and summarised the project back; only after the summary matched expectations did implementation begin.

**Models:**
Started with Claude Opus 4.7 (default for Max account). Switched to Sonnet 4.6 for routine implementation work after the orientation step — the structured CLAUDE.md and sub-agent files made Sonnet sufficient for boilerplate and structural tasks.

**What worked:**
- Forcing an orientation step ("read everything, summarise, don't write anything") before implementation — Sonnet's summary matched the spec almost line-for-line, which validated the up-front investment in CLAUDE.md.
- Acting as a named sub-agent in the prompt ("Acting as the data-collector sub-agent...") gave focused, in-scope output.
- "Show me the file contents, don't run the smoke test" stopped Claude Code from over-reaching past the prompt.

**What didn't work / had to be corrected:**
- The initial `.gitignore` had a too-broad `data/` rule that silently excluded `backend/app/data/__init__.py`. Caught by `git check-ignore -v`. Narrowed to `backend/data/`.
- Heredoc with triple-backticks confused bash; switched to `nano` for files containing markdown code fences.

**Lessons:**
- Always verify what git is *not* committing, not just what it is.
- Prefer `nano` over heredoc when authoring markdown that contains code blocks.
- Sub-agent files pay for themselves on the very first implementation prompt.

## Lessons learned

To be appended as lessons accumulate.

## Setup notes (for reproducibility)

- Anthropic Claude API key required (ANTHROPIC_API_KEY in .env).
- Claude Code installed on the development machine (Raspberry Pi in this case, but any Linux/macOS environment works).
- The sub-agent files in .claude/agents/ are picked up automatically by Claude Code.
