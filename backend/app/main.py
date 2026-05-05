import asyncio
import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.api.agent import router as agent_router
from app.api.traffic import router as traffic_router
from app.api.weather import router as weather_router
from app.core.config import settings
from app.data.vegvesen_scheduler import vegvesen_fetcher_loop
from app.db.session import engine

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the data directory exists before SQLite tries to open the file
    db_path = pathlib.Path(settings.database_url.removeprefix("sqlite:///"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create tables on first run; no-op if they already exist
    SQLModel.metadata.create_all(engine)
    logger.info("weather_traffic backend starting up — database ready at %s", db_path)

    fetcher_task = asyncio.create_task(vegvesen_fetcher_loop())
    logger.info(
        "vegvesen_fetcher: scheduled, interval=%ds",
        settings.vegvesen_fetch_interval_seconds,
    )

    yield

    fetcher_task.cancel()
    try:
        await fetcher_task
    except asyncio.CancelledError:
        pass

    logger.info("weather_traffic backend shutting down")


app = FastAPI(
    title="weather_traffic",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(weather_router, prefix="/api")
app.include_router(traffic_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.0.1"}
