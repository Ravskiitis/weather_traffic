from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from app.db.schema import IncidentStatus, TrafficIncident, WeatherIncidentLink, WeatherSnapshot


def upsert_weather_snapshot(session: Session, snapshot: WeatherSnapshot) -> WeatherSnapshot:
    """Insert snapshot; return existing row if (source, fetched_at, location_name) already present."""
    existing = session.exec(
        select(WeatherSnapshot).where(
            WeatherSnapshot.source == snapshot.source,
            WeatherSnapshot.fetched_at == snapshot.fetched_at,
            WeatherSnapshot.location_name == snapshot.location_name,
        )
    ).first()
    if existing:
        return existing
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def upsert_traffic_incident(session: Session, incident: TrafficIncident) -> TrafficIncident:
    """Insert or update incident on (source, external_id). Mutable fields are always refreshed."""
    existing = session.exec(
        select(TrafficIncident).where(
            TrafficIncident.source == incident.source,
            TrafficIncident.external_id == incident.external_id,
        )
    ).first()
    if existing:
        # Status, severity, ended_at, and description can change between fetches
        existing.status = incident.status
        existing.severity = incident.severity
        existing.ended_at = incident.ended_at
        existing.description = incident.description
        existing.fetched_at = incident.fetched_at
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


def get_recent_weather(
    session: Session, location_name: str, hours: int = 24
) -> list[WeatherSnapshot]:
    """Return weather snapshots for a location over the last N hours, newest first."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for SQLite comparison
    cutoff = cutoff - timedelta(hours=hours)
    return list(
        session.exec(
            select(WeatherSnapshot)
            .where(
                WeatherSnapshot.location_name == location_name,
                WeatherSnapshot.timestamp >= cutoff,
            )
            .order_by(WeatherSnapshot.timestamp.desc())
        ).all()
    )


def get_active_incidents(session: Session) -> list[TrafficIncident]:
    """Return all incidents with status=active, newest first."""
    return list(
        session.exec(
            select(TrafficIncident)
            .where(TrafficIncident.status == IncidentStatus.active)
            .order_by(TrafficIncident.started_at.desc())
        ).all()
    )


def get_incidents_with_weather(
    session: Session, days: int = 7
) -> list[tuple[TrafficIncident, Optional[WeatherSnapshot]]]:
    """Return incidents from the last N days paired with their weather-at-start snapshot (if any).

    Uses N+1 queries intentionally — this function is called infrequently (AI analyst, not hot path).
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    incidents = list(
        session.exec(
            select(TrafficIncident)
            .where(TrafficIncident.started_at >= cutoff)
            .order_by(TrafficIncident.started_at.desc())
        ).all()
    )

    result: list[tuple[TrafficIncident, Optional[WeatherSnapshot]]] = []
    for incident in incidents:
        link = session.exec(
            select(WeatherIncidentLink).where(
                WeatherIncidentLink.incident_id == incident.id,
                WeatherIncidentLink.weather_at_start == True,  # noqa: E712
            )
        ).first()
        weather = session.get(WeatherSnapshot, link.weather_snapshot_id) if link else None
        result.append((incident, weather))

    return result
