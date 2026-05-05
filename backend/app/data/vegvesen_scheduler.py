import asyncio
import logging
import time

import anyio
import httpx
from sqlmodel import Session

from app.core.config import settings
from app.data.vegvesen import VegvesenAuthMissing, fetch_active_incidents
from app.db.repositories import upsert_traffic_incident
from app.db.session import engine

logger = logging.getLogger(__name__)


async def vegvesen_fetcher_loop() -> None:
    """Infinite fetch-and-persist loop; cancels cleanly on asyncio.CancelledError."""
    while True:
        t0 = time.monotonic()
        try:
            incidents = await fetch_active_incidents()
            fetched = len(incidents)

            def _persist() -> int:
                with Session(engine) as session:
                    for incident in incidents:
                        upsert_traffic_incident(session, incident)
                return len(incidents)

            persisted = await anyio.to_thread.run_sync(_persist)
            duration = time.monotonic() - t0
            logger.info(
                "vegvesen_fetcher: fetched=%d persisted=%d duration=%.1fs",
                fetched,
                persisted,
                duration,
            )
        except asyncio.CancelledError:
            raise
        except VegvesenAuthMissing:
            logger.warning("vegvesen_fetcher: credentials missing, skipping")
        except httpx.HTTPStatusError as exc:
            logger.error(
                "vegvesen_fetcher: HTTP error status_code=%d", exc.response.status_code
            )
        except RuntimeError as exc:
            logger.error("vegvesen_fetcher: retries exhausted — %s", exc)
        except ValueError as exc:
            logger.error("vegvesen_fetcher: XML parse failure — %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("vegvesen_fetcher: unexpected error — %s", exc)

        await asyncio.sleep(settings.vegvesen_fetch_interval_seconds)
