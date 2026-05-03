import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.data.met_norway import fetch_current_weather
from app.db.repositories import upsert_weather_snapshot
from app.db.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current")
async def get_current_weather(
    session: Annotated[Session, Depends(get_session)],
):
    """Return the latest Bergen weather snapshot, fetching fresh data from MET Norway.

    Persists the result via upsert so the DB always holds the most recent reading.
    Returns HTTP 503 if the upstream fetch or DB write fails.
    """
    try:
        snapshot = await fetch_current_weather()
        saved = upsert_weather_snapshot(session, snapshot)
        return saved
    except Exception as exc:
        logger.error("GET /weather/current failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"error": "weather_unavailable", "detail": str(exc)},
        )
