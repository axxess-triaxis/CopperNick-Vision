"""Data shapes shared across the data loaders, agent, and web layer."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CycloneTrackPoint(BaseModel):
    """One observation from an IBTrACS storm track."""

    storm_id: str = Field(description="IBTrACS SID")
    name: str
    timestamp: datetime
    lat: float
    lon: float
    wind_knots: float | None = Field(default=None, description="USA_WIND, knots")
    pressure_mb: float | None = Field(default=None, description="USA_PRES, millibars")


class WeatherSnapshot(BaseModel):
    """A live Open-Meteo forecast point."""

    lat: float
    lon: float
    hourly_precipitation_mm: list[float]
    hourly_wind_speed_kmh: list[float]
    hourly_times: list[datetime]


class InfrastructureRiskAssessment(BaseModel):
    """The agent's judgment on cyclone/infrastructure risk for one region.

    Forced as a Gemini structured response, mirroring the pattern used
    elsewhere in this org's codebase: the model reasons, the rest of the
    pipeline treats the result as data, not prose to re-parse.
    """

    summary: str = Field(description="Plain-language risk summary, 2-3 sentences")
    risk_level: str = Field(description="One of: low, moderate, high, severe")
    likely_impacts: list[str] = Field(
        default_factory=list, description="Concrete, specific expected impacts"
    )
    advisory_text: str = Field(
        description="Draft early-warning advisory text for local authorities"
    )
    confidence_caveats: str = Field(
        description="What this assessment does NOT account for -- e.g. no physical "
        "storm-surge simulation, historical-track-based inference only"
    )
