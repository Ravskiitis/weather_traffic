import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.data.vegvesen import VegvesenAuthMissing, fetch_active_incidents
from app.db.repositories import get_active_incidents, upsert_traffic_incident
from app.db.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/incidents")
def get_incidents(
    session: Annotated[Session, Depends(get_session)],
):
    """Return all currently active traffic incidents in the Bergen region from the DB.

    Sync route — FastAPI runs it in a thread pool, keeping the event loop free.
    """
    try:
        return get_active_incidents(session)
    except Exception as exc:
        logger.error("GET /traffic/incidents failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"error": "db_unavailable", "detail": str(exc)},
        )


@router.post("/refresh")
async def refresh_incidents(
    session: Annotated[Session, Depends(get_session)],
):
    """Fetch fresh situation data from Vegvesen Datex II, upsert, and report the count.

    Async route because the upstream HTTP fetch is async (httpx).
    The sync upsert calls inside are acceptable for SQLite at this scale.
    """
    try:
        incidents = await fetch_active_incidents()
        for incident in incidents:
            upsert_traffic_incident(session, incident)
        logger.info("POST /traffic/refresh — upserted %d incidents", len(incidents))
        return {"upserted": len(incidents)}
    except VegvesenAuthMissing as exc:
        logger.warning("POST /traffic/refresh — credentials missing: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": "vegvesen_unauthorized",
                "detail": "Vegvesen DATEX II credentials not configured. See README.",
            },
        )
    except Exception as exc:
        logger.error("POST /traffic/refresh failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"error": "traffic_unavailable", "detail": str(exc)},
        )
