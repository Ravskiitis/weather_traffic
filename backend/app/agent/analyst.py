import asyncio
import json
import logging
import pathlib
import re
from datetime import datetime
from typing import Optional

from sqlalchemy import or_
from sqlmodel import Session, select

from app.agent import claude_client
from app.agent.claude_client import CLAUDE_MODEL
from app.agent.models import Report, ReportInput, ReportSection
from app.agent.prompts import ACTIVE_SYSTEM_PROMPT, build_user_message
from app.db.schema import IncidentStatus, TrafficIncident, WeatherSnapshot
from app.db.session import engine

logger = logging.getLogger(__name__)

_LOG_DIR = pathlib.Path("data/agent_logs")


# ---------------------------------------------------------------------------
# DB extraction helpers — called while the session is still open
# ---------------------------------------------------------------------------


def _snapshot_to_dict(snap: WeatherSnapshot) -> dict:
    return {
        "timestamp": snap.timestamp.isoformat() if snap.timestamp else None,
        "fetched_at": snap.fetched_at.isoformat() if snap.fetched_at else None,
        "location_name": snap.location_name,
        "temperature_c": snap.temperature_c,
        "feels_like_c": snap.feels_like_c,
        "wind_speed_ms": snap.wind_speed_ms,
        "wind_direction_deg": snap.wind_direction_deg,
        "humidity_pct": snap.humidity_pct,
        "pressure_hpa": snap.pressure_hpa,
        "precipitation_mm_h": snap.precipitation_mm_h,
        "weather_symbol": snap.weather_symbol,
        "source": snap.source,
    }


def _incident_to_dict(inc: TrafficIncident) -> dict:
    return {
        "external_id": inc.external_id,
        "source": inc.source,
        "incident_type": inc.incident_type,
        "location_name": inc.location_name,
        "road_ref": inc.road_ref,
        "latitude": inc.latitude,
        "longitude": inc.longitude,
        "severity": inc.severity,
        "status": inc.status,
        "started_at": inc.started_at.isoformat() if inc.started_at else None,
        "ended_at": inc.ended_at.isoformat() if inc.ended_at else None,
        "description": inc.description,
    }


# ---------------------------------------------------------------------------
# JSON extraction — tolerates prose or code fences around the JSON object
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a string, stripping any surrounding prose."""
    # Common case: clean JSON with possible leading/trailing whitespace
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Fallback 1: strip markdown code fences (```json ... ``` or ``` ... ```)
    fenced = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass

    # Fallback 2: find the first {...} block in case there is surrounding prose
    match = re.search(r"\{.*\}", fenced, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    truncation_hint = (
        " — response appears truncated, consider increasing max_tokens"
        if not text.strip().endswith("}")
        else ""
    )
    raise ValueError(
        f"Could not parse Claude response as JSON{truncation_hint}. "
        f"First 200 chars: {text[:200]!r}"
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _write_log(system: str, user: str, response: str) -> None:
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        path = _LOG_DIR / f"{ts}.json"
        path.write_text(
            json.dumps(
                {"timestamp": ts, "system": system, "user": user, "response": response},
                ensure_ascii=False,
                indent=2,
            )
        )
    except Exception as exc:
        logger.warning("Could not write agent log: %s", exc)


# ---------------------------------------------------------------------------
# Degraded report factory
# ---------------------------------------------------------------------------


def _degraded_report(language: str, reason: str) -> Report:
    logger.error("Returning degraded report: %s", reason)
    return Report(
        generated_at=datetime.utcnow(),
        model=CLAUDE_MODEL,
        confidence=0.0,
        language=language,  # type: ignore[arg-type]
        summary="AI analysis temporarily unavailable.",
        sections=[],
        sources=[f"error: {reason}"],
        referenced_entities=[],
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def generate_report(language: str = "en") -> Report:
    """Generate an operational weather-traffic report for Bergen.

    Reads latest WeatherSnapshot and active/monitored TrafficIncidents from the DB,
    builds a prompt, calls Claude, and parses the structured JSON response.

    Always returns a Report — returns a degraded one (confidence=0) on any failure.
    """
    # --- 1. Read DB data (sync session, fast SQLite reads are fine in async context) ---
    weather_dict: Optional[dict] = None
    incident_dicts: list[dict] = []

    try:
        with Session(engine) as session:
            latest_snap = session.exec(
                select(WeatherSnapshot)
                .where(
                    WeatherSnapshot.source == "met_norway",
                    WeatherSnapshot.location_name == "Bergen sentrum",
                )
                .order_by(WeatherSnapshot.fetched_at.desc())
            ).first()

            active_incidents = list(
                session.exec(
                    select(TrafficIncident)
                    .where(
                        or_(
                            TrafficIncident.status == IncidentStatus.active,
                            TrafficIncident.status == IncidentStatus.monitoring,
                        )
                    )
                    .order_by(TrafficIncident.started_at.desc())
                ).all()
            )

            # Extract primitives while the session is open
            if latest_snap:
                weather_dict = _snapshot_to_dict(latest_snap)
            incident_dicts = [_incident_to_dict(i) for i in active_incidents]

    except Exception as exc:
        return _degraded_report(language, f"DB read failed: {exc}")

    logger.info(
        "generate_report — weather=%s incidents=%d language=%s",
        "present" if weather_dict else "missing",
        len(incident_dicts),
        language,
    )

    # --- 2. Build prompt ---
    report_input = ReportInput(
        weather=weather_dict,
        incidents=incident_dicts,
        language=language,  # type: ignore[arg-type]
    )
    system_prompt = ACTIVE_SYSTEM_PROMPT
    user_message = build_user_message(report_input)

    # --- 3. Call Claude (sync SDK → thread so we don't block the event loop) ---
    try:
        raw_response: str = await asyncio.to_thread(
            claude_client.call_model, system_prompt, user_message, 4096
        )
    except Exception as exc:
        _write_log(system_prompt, user_message, f"ERROR: {exc}")
        return _degraded_report(language, f"Claude API call failed: {exc}")

    _write_log(system_prompt, user_message, raw_response)
    logger.debug("Claude raw response (first 200 chars): %r", raw_response[:200])

    # --- 4. Parse response ---
    try:
        data = _extract_json(raw_response)
        report = Report(
            generated_at=datetime.utcnow(),
            model=CLAUDE_MODEL,
            confidence=float(data.get("confidence", 0.5)),
            language=data.get("language", language),  # type: ignore[arg-type]
            summary=data.get("summary", ""),
            sections=[ReportSection(**s) for s in data.get("sections", [])],
            sources=data.get("sources", []),
            referenced_entities=data.get("referenced_entities", []),
        )
    except Exception as exc:
        logger.error("Failed to parse Claude response: %s — raw: %r", exc, raw_response[:300])
        return _degraded_report(language, f"Response parse failed: {exc}")

    logger.info(
        "Report generated — confidence=%.2f sections=%d entities=%d",
        report.confidence,
        len(report.sections),
        len(report.referenced_entities),
    )
    return report
