from sqlmodel import Session, create_engine

from app.core.config import settings

# Sync engine — SQLite async (aiosqlite) adds complexity without meaningful benefit
# at this scale (single-region, low write concurrency on a Raspberry Pi).
# FastAPI routes that access the DB should be declared as plain (sync) functions;
# FastAPI will automatically run them in a thread-pool executor, keeping the
# event loop free.  Async routes that need DB access can use
# anyio.to_thread.run_sync() if necessary.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # required for SQLite + thread-pool use
    echo=False,
)


def get_session():
    """FastAPI dependency that yields a SQLModel session and auto-commits on exit."""
    with Session(engine) as session:
        yield session
