import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.agent.analyst import generate_report
from app.agent.models import Report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

# ---------------------------------------------------------------------------
# In-memory report cache — single slot, 15-minute TTL.
# TODO: persist the latest report to DB so it survives restarts and is queryable
# for the correlation chart (7-day report history).
# ---------------------------------------------------------------------------

_cached_report: Optional[Report] = None
_cache_at: Optional[datetime] = None
_CACHE_TTL = timedelta(minutes=15)


@router.post("/report")
async def create_report(language: str = "en") -> Report:
    """Generate a fresh AI report for the Bergen region and cache it.

    language: "en" (default) or "no". Returns a degraded report (confidence=0)
    rather than an error if the Claude API or DB is unavailable.
    """
    global _cached_report, _cache_at

    if language not in ("en", "no"):
        raise HTTPException(status_code=422, detail="language must be 'en' or 'no'")

    report = await generate_report(language=language)
    _cached_report = report
    _cache_at = datetime.utcnow()
    logger.info("POST /agent/report — confidence=%.2f language=%s", report.confidence, language)
    return report


@router.get("/report/latest")
async def get_latest_report() -> Report:
    """Return the most recently generated report.

    Returns 404 if no report has been generated since the server started.
    The cache is not invalidated by TTL on reads — call POST /agent/report to refresh.
    """
    if _cached_report is None:
        raise HTTPException(
            status_code=404,
            detail="No report has been generated yet. Call POST /api/agent/report first.",
        )

    age_minutes = (
        round((datetime.utcnow() - _cache_at).total_seconds() / 60, 1)
        if _cache_at
        else None
    )
    logger.info("GET /agent/report/latest — age=%.1f min", age_minutes or 0)
    return _cached_report
