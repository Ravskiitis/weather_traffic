from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    title: Literal["situation", "impact", "recommendations", "outlook"]
    content: str


class Report(BaseModel):
    generated_at: datetime
    model: str
    confidence: float = Field(ge=0.0, le=1.0)
    language: Literal["no", "en"]
    summary: str
    sections: list[ReportSection]
    sources: list[str]
    referenced_entities: list[str]


class ReportInput(BaseModel):
    """Structured snapshot of DB data to feed the analyst prompt."""

    weather: Optional[dict] = None  # WeatherSnapshot fields as plain dict
    incidents: list[dict] = Field(default_factory=list)  # TrafficIncident fields as plain dicts
    language: Literal["no", "en"] = "en"
    region: str = "bergen"
