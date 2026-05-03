import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import settings
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
    yield
    logger.info("weather_traffic backend shutting down")


app = FastAPI(
    title="weather_traffic",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Astro dev server; extend for production origin once known
    allow_origins=["http://localhost:4321"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.0.1"}
