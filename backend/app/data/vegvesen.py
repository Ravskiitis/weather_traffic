import asyncio
import logging
import time
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree as ET

import httpx
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.db.schema import IncidentSeverity, IncidentStatus, TrafficIncident

logger = logging.getLogger(__name__)

BERGEN_BBOX = {"min_lat": 60.2, "max_lat": 60.6, "min_lon": 4.9, "max_lon": 5.7}

# TODO: Verify this URL against the current Vegvesen ATLAS developer portal before production use.
# Rationale: datex-server-get-v3-1 → Datex II v3.1, pull (client-initiated) model.
# /datexapi/GetSituation/pullsnapshotdata is the standard Datex II v3 snapshot path.
# Fallbacks to try if this returns 404 or empty:
#   https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/SituationPublication/pullsnapshotdata
#   https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/situation
_SITUATION_URL = (
    "https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/GetSituation/pullsnapshotdata"
)
_MAX_ATTEMPTS = 3
_SOURCE = "vegvesen_datex2"


class VegvesenAuthMissing(Exception):
    """Raised when VEGVESEN_USERNAME / VEGVESEN_PASSWORD are not configured."""


# ---------------------------------------------------------------------------
# Pydantic intermediate model
# Fields are populated from XML extraction; all optional with fallbacks because
# the exact Datex II field paths are not confirmed against a live Vegvesen response.
# ---------------------------------------------------------------------------


class _RawSituation(BaseModel):
    """Structured data extracted from one Datex II <situation> element.

    Serves as a validated checkpoint between raw XML strings and the TrafficIncident
    schema. Fields use wide Optional[...] types because Vegvesen's XML dialect may
    encode the same concept in different element names than the Datex II standard.

    TODO: Tighten field types once a live response has been inspected.
    """

    model_config = ConfigDict(extra="ignore")

    external_id: str
    incident_type_raw: str = "unknown"  # raw xsi:type or element name from Datex II
    lat: float
    lon: float
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    severity_text: Optional[str] = None
    description: Optional[str] = None
    location_name: str = "Bergen region"
    road_ref: Optional[str] = None


# ---------------------------------------------------------------------------
# XML helpers — namespace-agnostic so the code survives namespace mismatches
# ---------------------------------------------------------------------------


def _local(tag: str) -> str:
    """Strip XML namespace URI from a tag: '{http://...}name' → 'name'."""
    return tag.split("}")[-1] if "}" in tag else tag


def _find_text(element: ET.Element, *local_names: str) -> Optional[str]:
    """Depth-first search for the first descendant whose local tag is in local_names."""
    for child in element.iter():
        if _local(child.tag) in local_names and child.text:
            return child.text.strip()
    return None


def _find_float(element: ET.Element, *local_names: str) -> Optional[float]:
    text = _find_text(element, *local_names)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_dt(text: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string to a naive UTC datetime."""
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)  # strip tz — store naive UTC (project-wide convention)
    except ValueError:
        logger.debug("Could not parse datetime: %r", text)
        return None


# ---------------------------------------------------------------------------
# Type and severity mapping
# ---------------------------------------------------------------------------


def _map_incident_type(raw_type: str) -> str:
    """Map a Datex II situation record type string to our incident_type values.

    Matching is substring-based (case-insensitive) so it handles both standard Datex II
    type names and any Vegvesen extension types (e.g. 'VegvesenTunnelClosure').

    TODO: Refine after reviewing real Vegvesen xsi:type values in a live response.
    The mapping for tunnel_closure and wind_warning in particular may need adjusting.
    """
    t = raw_type.lower()
    if "accident" in t:
        return "accident"
    if "tunnel" in t:
        return "tunnel_closure"
    if "roadwork" in t or "maintenance" in t or "construction" in t:
        return "roadworks"
    if "wind" in t or "storm" in t or "weather" in t or "abnormal" in t:
        return "wind_warning"
    return "other"


def _map_severity(severity_text: Optional[str]) -> IncidentSeverity:
    """Map Datex II overallSeverity string to our IncidentSeverity enum.

    Known Datex II v3 values: lowestImpact, low, normal, high, highest, severe.
    TODO: Confirm which values Vegvesen actually emits in this feed.
    """
    if not severity_text:
        return IncidentSeverity.low
    s = severity_text.lower()
    if s in ("high", "highest", "severe"):
        return IncidentSeverity.high
    if s in ("normal", "medium"):
        return IncidentSeverity.medium
    return IncidentSeverity.low


# ---------------------------------------------------------------------------
# Coordinate extraction
# ---------------------------------------------------------------------------


def _extract_coords(element: ET.Element) -> Optional[tuple[float, float]]:
    """Try to pull (latitude, longitude) from an element or its descendants.

    Datex II v3 encodes coordinates in several possible structures:
      - <locationForDisplay><latitude> + <longitude>
      - <pointCoordinates><latitude> + <longitude>
      - <coordinates><latitude> + <longitude>

    Using _find_float scans all descendants, so we hit whichever structure is used.

    TODO: After inspecting a live response, narrow this to the exact path to avoid
    accidentally picking up unrelated numeric fields.
    """
    lat = _find_float(element, "latitude")
    lon = _find_float(element, "longitude")
    if lat is not None and lon is not None:
        return lat, lon
    return None


def _in_bergen_bbox(lat: float, lon: float) -> bool:
    return (
        BERGEN_BBOX["min_lat"] <= lat <= BERGEN_BBOX["max_lat"]
        and BERGEN_BBOX["min_lon"] <= lon <= BERGEN_BBOX["max_lon"]
    )


# ---------------------------------------------------------------------------
# Per-situation parsing
# ---------------------------------------------------------------------------


def _extract_raw(situation_el: ET.Element) -> Optional[_RawSituation]:
    """Extract structured data from a single <situation> element.

    Returns None if:
      - No external_id found
      - No <situationRecord> child found
      - No coordinates found (required for bbox filter)

    TODO: The element names used here match the Datex II v3 standard schema.
    Confirm against a live Vegvesen response — especially:
      - The attribute name carrying the situation's ID ('id', 'situationId', etc.)
      - Whether records are named 'situationRecord' or something else
      - Whether xsi:type is used for type discrimination or a separate element
      - The exact element path for coordinates
    """
    # Situation ID — Datex II v3 uses an 'id' attribute on <situation>
    external_id = (
        situation_el.get("id")
        or situation_el.get("situationId")
        or _find_text(situation_el, "situationId", "id")
    )
    if not external_id:
        logger.debug("Skipping <situation> with no recognisable ID")
        return None

    # Find first <situationRecord> child
    record_el: Optional[ET.Element] = None
    for child in situation_el:
        if _local(child.tag) == "situationRecord":
            record_el = child
            break

    if record_el is None:
        logger.debug("Situation %s has no <situationRecord> — skipping", external_id)
        return None

    # Incident type: Datex II encodes record type in xsi:type attribute
    xsi_type = record_el.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
    if not xsi_type:
        # Fallback: plain 'type' attribute, or the element's own local name
        xsi_type = record_el.get("type", "") or _local(record_el.tag)

    # Coordinates — check both the situation element and the record element
    coords = _extract_coords(situation_el) or _extract_coords(record_el)
    if coords is None:
        logger.debug("Situation %s has no coordinates — skipping", external_id)
        return None
    lat, lon = coords

    return _RawSituation(
        external_id=external_id,
        incident_type_raw=xsi_type,
        lat=lat,
        lon=lon,
        started_at=_parse_dt(
            _find_text(record_el, "startTime", "overallStartTime", "startOfPeriod")
        ),
        ended_at=_parse_dt(
            _find_text(record_el, "endTime", "overallEndTime", "endOfPeriod")
        ),
        severity_text=_find_text(situation_el, "overallSeverity", "severity"),
        description=_find_text(
            record_el, "comment", "generalPublicComment", "description", "headline"
        ),
        location_name=(
            _find_text(record_el, "locationName", "areaName", "name") or "Bergen region"
        ),
        road_ref=_find_text(record_el, "roadNumber", "roadIdentifier", "roadName"),
    )


def _to_traffic_incident(raw: _RawSituation, fetched_at: datetime) -> TrafficIncident:
    """Convert a validated _RawSituation to a TrafficIncident DB row."""
    now = datetime.utcnow()
    started_at = raw.started_at or fetched_at

    if raw.ended_at is not None and raw.ended_at < now:
        status = IncidentStatus.closed
    elif started_at > now:
        status = IncidentStatus.scheduled
    else:
        status = IncidentStatus.active

    return TrafficIncident(
        external_id=raw.external_id,
        source=_SOURCE,
        incident_type=_map_incident_type(raw.incident_type_raw),
        location_name=raw.location_name,
        road_ref=raw.road_ref,
        latitude=raw.lat,
        longitude=raw.lon,
        severity=_map_severity(raw.severity_text),
        started_at=started_at,
        ended_at=raw.ended_at,
        description=raw.description,
        status=status,
        fetched_at=fetched_at,
    )


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------


async def fetch_active_incidents() -> list[TrafficIncident]:
    """Fetch all active Bergen-region traffic situations from the Vegvesen Datex II feed.

    Pulls the national snapshot, parses XML, filters to the Bergen bounding box,
    and returns only records with usable coordinates.

    Retries up to _MAX_ATTEMPTS times with exponential backoff on 5xx / network errors.
    Raises VegvesenAuthMissing if credentials are not configured.
    """
    if not settings.vegvesen_username or not settings.vegvesen_password:
        raise VegvesenAuthMissing(
            "Vegvesen DATEX II credentials not configured — register at "
            "https://www.vegvesen.no/en/fag/technology/open-data/"
            "a-selection-of-open-data/what-is-datex/get-access/"
        )
    auth = httpx.BasicAuth(settings.vegvesen_username, settings.vegvesen_password)

    timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
    raw: Optional[httpx.Response] = None
    last_exc: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=timeout, auth=auth) as client:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            t0 = time.monotonic()
            try:
                raw = await client.get(_SITUATION_URL)
                raw.raise_for_status()
                duration = round(time.monotonic() - t0, 2)
                logger.info(
                    "Vegvesen Datex II fetch ok — attempt=%d status=%d duration=%.2fs",
                    attempt,
                    raw.status_code,
                    duration,
                )
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise  # 4xx — do not retry
                last_exc = exc
                logger.warning(
                    "Vegvesen HTTP %d (attempt %d/%d)",
                    exc.response.status_code,
                    attempt,
                    _MAX_ATTEMPTS,
                )
            except (httpx.NetworkError, httpx.TimeoutException) as exc:
                last_exc = exc
                logger.warning(
                    "Vegvesen network error (attempt %d/%d): %s",
                    attempt,
                    _MAX_ATTEMPTS,
                    exc,
                )
            if attempt < _MAX_ATTEMPTS:
                await asyncio.sleep(2**attempt)  # 2 s, 4 s
        else:
            raise RuntimeError(
                f"Vegvesen Datex II fetch failed after {_MAX_ATTEMPTS} attempts"
            ) from last_exc

    # TODO: During first integration test, log the root element tag to confirm namespace:
    #   logger.debug("Vegvesen XML root tag: %s", ET.fromstring(raw.content).tag)
    try:
        root = ET.fromstring(raw.content)
    except ET.ParseError as exc:
        raise ValueError(f"Vegvesen response is not valid XML: {exc}") from exc

    fetched_at = datetime.utcnow()
    incidents: list[TrafficIncident] = []
    total = skipped_no_id = skipped_no_coords = skipped_bbox = 0

    for el in root.iter():
        if _local(el.tag) != "situation":
            continue
        total += 1

        raw_sit = _extract_raw(el)
        if raw_sit is None:
            # _extract_raw already logged the reason
            skipped_no_id += 1
            continue

        if not _in_bergen_bbox(raw_sit.lat, raw_sit.lon):
            skipped_bbox += 1
            continue

        incidents.append(_to_traffic_incident(raw_sit, fetched_at))

    logger.info(
        "Vegvesen parse — total=%d bergen=%d skipped_no_data=%d skipped_outside_bbox=%d",
        total,
        len(incidents),
        skipped_no_id,
        skipped_bbox,
    )
    return incidents
