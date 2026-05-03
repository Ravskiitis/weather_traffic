#!/usr/bin/env python3
"""Seed realistic demo traffic incidents for the Bergen region.

Run from the backend directory:
    cd backend && python scripts/seed_demo.py

Idempotent — re-running will not duplicate rows (upserts on source + external_id).
Uses source="demo_seed" so live Vegvesen data stays separable.
"""

import pathlib
import sys

# Make 'app' importable when invoked as  cd backend && python scripts/seed_demo.py
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Load .env from the project root (one level above backend/)
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent.parent.parent / ".env")

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlmodel import SQLModel, Session

from app.db.schema import IncidentSeverity, IncidentStatus, TrafficIncident
from app.db.session import engine
from app.db.repositories import upsert_traffic_incident

# Ensure tables exist (no-op if already created by the main app)
SQLModel.metadata.create_all(engine)

_SOURCE = "demo_seed"


def _ago(hours: float = 0, minutes: float = 0) -> datetime:
    """Return a naive UTC datetime N hours/minutes in the past."""
    delta = timedelta(hours=hours, minutes=minutes)
    return (datetime.now(timezone.utc) - delta).replace(tzinfo=None)


INCIDENTS: list[dict] = [
    # ---- accidents (2) --------------------------------------------------
    {
        "external_id": "demo-accident-001",
        "incident_type": "accident",
        "location_name": "E39 nordgående ved Nygårdstangen",
        "road_ref": "E39",
        "latitude": 60.388,
        "longitude": 5.318,
        "severity": IncidentSeverity.high,
        "started_at": _ago(minutes=45),
        "ended_at": None,
        "description": "Trafikkulykke i nordgående felt, ett felt sperret. Kø tilbake til Fjøsanger.",
        "status": IncidentStatus.active,
    },
    {
        "external_id": "demo-accident-002",
        "incident_type": "accident",
        "location_name": "E16 Arna vestgående",
        "road_ref": "E16",
        "latitude": 60.401,
        "longitude": 5.476,
        "severity": IncidentSeverity.medium,
        "started_at": _ago(hours=2, minutes=30),
        "ended_at": None,
        "description": "Påkjørsel bakfra, begge felt åpne. Forsinkelser forventes.",
        "status": IncidentStatus.active,
    },
    # ---- tunnel closures (2) --------------------------------------------
    {
        "external_id": "demo-tunnel-001",
        "incident_type": "tunnel_closure",
        "location_name": "Eikåstunnelen — Rv580",
        "road_ref": "Rv580",
        "latitude": 60.372,
        "longitude": 5.334,
        "severity": IncidentSeverity.low,
        "started_at": _ago(hours=6),
        "ended_at": None,
        "description": "Eikåstunnelen stengt for all trafikk — ventilasjonsanlegg under vedlikehold. Omkjøring via Nygårdsveien.",
        "status": IncidentStatus.active,
    },
    {
        "external_id": "demo-tunnel-002",
        "incident_type": "tunnel_closure",
        "location_name": "Fløyfjelltunnelen — Rv555",
        "road_ref": "Rv555",
        "latitude": 60.393,
        "longitude": 5.298,
        "severity": IncidentSeverity.medium,
        "started_at": _ago(hours=4),
        "ended_at": None,
        "description": "Fløyfjelltunnelen: redusert hastighet til 50 km/t, høyre felt sperret. Trafikklys i drift.",
        "status": IncidentStatus.monitoring,
    },
    # ---- roadworks (1) --------------------------------------------------
    {
        "external_id": "demo-roadworks-001",
        "incident_type": "roadworks",
        "location_name": "Damsgårdsveien ved Damsgårdstunnelen — Fv585",
        "road_ref": "Fv585",
        "latitude": 60.383,
        "longitude": 5.283,
        "severity": IncidentSeverity.low,
        "started_at": _ago(hours=18),
        "ended_at": None,
        "description": "Veiarbeid ved Damsgårdsveien, nattarbeid pågår. Trafikkregulering på stedet. Redusert fremkommelighet.",
        "status": IncidentStatus.active,
    },
    # ---- wind warnings (2) ----------------------------------------------
    {
        "external_id": "demo-wind-001",
        "incident_type": "wind_warning",
        "location_name": "Nordhordlandsbroen — E39",
        "road_ref": "E39",
        "latitude": 60.480,
        "longitude": 5.174,
        "severity": IncidentSeverity.high,
        "started_at": _ago(hours=1, minutes=30),
        "ended_at": None,
        "description": "Sterk vind ved Nordhordlandsbroen, vindkast opp til 25 m/s. Kjørefelt for høye kjøretøy og campingvogner stengt.",
        "status": IncidentStatus.active,
    },
    {
        "external_id": "demo-wind-002",
        "incident_type": "wind_warning",
        "location_name": "Puddefjordsbroen — Rv580",
        "road_ref": "Rv580",
        "latitude": 60.381,
        "longitude": 5.311,
        "severity": IncidentSeverity.medium,
        "started_at": _ago(minutes=30),
        "ended_at": None,
        "description": "Vindvarsel ved Puddefjordsbroen, kast opp til 18 m/s. Kjør forsiktig. Følg trafikkskiltene.",
        "status": IncidentStatus.active,
    },
    # ---- other (1) ------------------------------------------------------
    {
        "external_id": "demo-other-001",
        "incident_type": "other",
        "location_name": "E39 sørgående ved Fjøsanger",
        "road_ref": "E39",
        "latitude": 60.363,
        "longitude": 5.319,
        "severity": IncidentSeverity.low,
        "started_at": _ago(hours=12),
        "ended_at": _ago(hours=4),
        "description": "Fremmedlegeme i kjørebanen fjernet. Vei åpen for normal trafikk.",
        "status": IncidentStatus.closed,
    },
]


def main() -> None:
    fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)

    summaries: list[dict] = []
    with Session(engine) as session:
        for data in INCIDENTS:
            incident = TrafficIncident(
                source=_SOURCE,
                fetched_at=fetched_at,
                **data,
            )
            saved = upsert_traffic_incident(session, incident)
            # Extract all needed values while the session is still open.
            summaries.append({
                "incident_type": saved.incident_type,
                "severity": saved.severity,
                "status": saved.status,
                "location_name": saved.location_name,
                "saved": saved.id is not None,
            })

    print(f"\nSeeded {len(summaries)} demo incidents (source='{_SOURCE}'):\n")

    by_type = Counter(s["incident_type"] for s in summaries)
    by_severity = Counter(s["severity"] for s in summaries)
    by_status = Counter(s["status"] for s in summaries)

    print("  By type:    ", dict(by_type))
    print("  By severity:", dict(by_severity))
    print("  By status:  ", dict(by_status))
    print()
    for s in summaries:
        marker = "✓" if s["saved"] else "?"
        print(f"  {marker} [{s['incident_type']:15s}] {s['location_name']}")
    print()


if __name__ == "__main__":
    main()
