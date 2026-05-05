import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class IncidentStatus(str, enum.Enum):
    scheduled = "scheduled"
    active = "active"
    monitoring = "monitoring"
    closed = "closed"


class WeatherSnapshot(SQLModel, table=True):
    __tablename__ = "weather_snapshot"
    __table_args__ = (
        UniqueConstraint("source", "fetched_at", "location_name", name="uq_weather_source_time_loc"),
        Index("ix_weather_timestamp", "timestamp"),
        Index("ix_weather_location", "location_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime  # time the weather reading represents (UTC)
    location_name: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: Optional[float] = None
    wind_speed_ms: float
    wind_direction_deg: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    precipitation_mm_h: Optional[float] = None
    weather_symbol: Optional[str] = None  # MET Norway symbol code, e.g. "heavyrain"
    source: str  # e.g. "met_norway"
    fetched_at: datetime  # when this row was written (UTC)


class TrafficIncident(SQLModel, table=True):
    __tablename__ = "traffic_incident"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_incident_source_external"),
        Index("ix_incident_status", "status"),
        Index("ix_incident_started_at", "started_at"),
        Index("ix_incident_source", "source"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str  # ID assigned by the originating source
    source: str  # e.g. "vegvesen_datex2"
    incident_type: str  # accident | tunnel_closure | roadworks | wind_warning
    location_name: str
    road_ref: Optional[str] = None  # e.g. "E39", "Rv580"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: IncidentSeverity
    started_at: datetime  # UTC
    ended_at: Optional[datetime] = None  # UTC; None means still open
    description: Optional[str] = None
    status: IncidentStatus
    fetched_at: datetime  # when this row was last written (UTC)


class WeatherIncidentLink(SQLModel, table=True):
    """Ties a TrafficIncident to the WeatherSnapshot closest to its start time."""

    __tablename__ = "weather_incident_link"
    __table_args__ = (
        Index("ix_link_incident_id", "incident_id"),
        Index("ix_link_weather_id", "weather_snapshot_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="traffic_incident.id")
    weather_snapshot_id: int = Field(foreign_key="weather_snapshot.id")
    weather_at_start: bool = Field(default=True)  # True = snapshot was taken at incident start
