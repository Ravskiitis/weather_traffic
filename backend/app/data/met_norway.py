import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.db.schema import WeatherSnapshot

logger = logging.getLogger(__name__)

BERGEN_LAT: float = 60.39
BERGEN_LON: float = 5.32
LOCATION_NAME: str = "Bergen sentrum"

_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
_MAX_ATTEMPTS = 3


# ---------------------------------------------------------------------------
# Pydantic models — only the fields we actually use from the response.
# Full schema: https://api.met.no/weatherapi/locationforecast/2.0/swagger
# ---------------------------------------------------------------------------


class _InstantDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")

    air_temperature: float
    wind_speed: float
    wind_from_direction: Optional[float] = None
    relative_humidity: Optional[float] = None
    air_pressure_at_sea_level: Optional[float] = None


class _Instant(BaseModel):
    model_config = ConfigDict(extra="ignore")

    details: _InstantDetails


class _Next1HoursSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol_code: Optional[str] = None


class _Next1HoursDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")

    precipitation_amount: Optional[float] = None


class _Next1Hours(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: Optional[_Next1HoursSummary] = None
    details: Optional[_Next1HoursDetails] = None


class _TimeseriesData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    instant: _Instant
    next_1_hours: Optional[_Next1Hours] = None


class _TimeseriesEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: datetime
    data: _TimeseriesData


class _Meta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    updated_at: datetime


class _Properties(BaseModel):
    model_config = ConfigDict(extra="ignore")

    meta: _Meta
    timeseries: list[_TimeseriesEntry]


class _METResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    properties: _Properties


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------


async def fetch_current_weather() -> WeatherSnapshot:
    """Fetch current Bergen weather from MET Norway Locationforecast 2.0 compact.

    Uses timeseries[0] (the current or most-recent analysis step) for instant values,
    and next_1_hours for precipitation and symbol if available.

    Retries up to _MAX_ATTEMPTS times with exponential backoff on 5xx / network errors.
    Raises immediately on 4xx (client error, no point retrying).
    """
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
    headers = {"User-Agent": settings.met_user_agent}
    params = {"lat": BERGEN_LAT, "lon": BERGEN_LON}

    raw: Optional[httpx.Response] = None
    last_exc: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            t0 = time.monotonic()
            try:
                raw = await client.get(_URL, params=params)
                raw.raise_for_status()
                duration = round(time.monotonic() - t0, 2)
                logger.info(
                    "MET Norway fetch ok — attempt=%d status=%d duration=%.2fs",
                    attempt,
                    raw.status_code,
                    duration,
                )
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise  # 4xx — client error, do not retry
                last_exc = exc
                logger.warning(
                    "MET Norway HTTP %d (attempt %d/%d)",
                    exc.response.status_code,
                    attempt,
                    _MAX_ATTEMPTS,
                )
            except (httpx.NetworkError, httpx.TimeoutException) as exc:
                last_exc = exc
                logger.warning(
                    "MET Norway network error (attempt %d/%d): %s",
                    attempt,
                    _MAX_ATTEMPTS,
                    exc,
                )

            if attempt < _MAX_ATTEMPTS:
                await asyncio.sleep(2**attempt)  # 2 s, 4 s
        else:
            raise RuntimeError(
                f"MET Norway fetch failed after {_MAX_ATTEMPTS} attempts"
            ) from last_exc

    parsed = _METResponse.model_validate(raw.json())
    props = parsed.properties

    if not props.timeseries:
        raise ValueError("MET Norway returned an empty timeseries")

    current = props.timeseries[0]
    details = current.data.instant.details
    n1h = current.data.next_1_hours

    # MET Norway datetimes are timezone-aware (UTC/Z). Strip tzinfo so all
    # datetimes stored in SQLite are naive UTC, consistent with the rest of the schema.
    def _naive(dt: datetime) -> datetime:
        return dt.replace(tzinfo=None)

    return WeatherSnapshot(
        timestamp=_naive(props.meta.updated_at),
        location_name=LOCATION_NAME,
        latitude=BERGEN_LAT,
        longitude=BERGEN_LON,
        temperature_c=details.air_temperature,
        feels_like_c=None,  # compact endpoint does not include apparent temperature
        wind_speed_ms=details.wind_speed,
        wind_direction_deg=details.wind_from_direction,
        humidity_pct=details.relative_humidity,
        pressure_hpa=details.air_pressure_at_sea_level,
        precipitation_mm_h=(n1h.details.precipitation_amount if (n1h and n1h.details) else None),
        weather_symbol=(n1h.summary.symbol_code if (n1h and n1h.summary) else None),
        source="met_norway",
        fetched_at=datetime.utcnow(),  # naive UTC, consistent with schema convention
    )
