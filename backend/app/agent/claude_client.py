import logging
import time
from typing import Optional

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

# Verified against https://docs.anthropic.com/en/docs/about-claude/models on 2026-05-03.
# Update when a newer Sonnet is released; check the URL above before changing.
CLAUDE_MODEL = "claude-sonnet-4-6"

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set — add it to .env before generating reports"
            )
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def call_model(system: str, user: str, max_tokens: int = 4096) -> str:
    """Call the Claude API synchronously and return the text response.

    Designed to be called via asyncio.to_thread() from async contexts so the
    event loop is not blocked during the network round-trip.

    4096 tokens comfortably fits a 4-section operational report (~600–900 words of JSON).
    """
    client = _get_client()
    t0 = time.monotonic()

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    duration = round(time.monotonic() - t0, 2)
    usage = response.usage
    logger.info(
        "Claude call — model=%s input_tokens=%d output_tokens=%d duration=%.2fs",
        CLAUDE_MODEL,
        usage.input_tokens,
        usage.output_tokens,
        duration,
    )

    return response.content[0].text
