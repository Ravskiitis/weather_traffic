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

To be appended as the project progresses. Each entry: date, sub-agent, what was attempted, what worked, what didn't.

## Lessons learned

To be appended as lessons accumulate.

## Setup notes (for reproducibility)

- Anthropic Claude API key required (ANTHROPIC_API_KEY in .env).
- Claude Code installed on the development machine (Raspberry Pi in this case, but any Linux/macOS environment works).
- The sub-agent files in .claude/agents/ are picked up automatically by Claude Code.
