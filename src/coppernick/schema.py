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


class SkyObjectClass(str):
    """Free-text but constrained-by-prompt category for a detected aerial object.

    Intentionally a plain str subtype, not an Enum: the vocabulary (bird,
    aircraft, weather-balloon, drone, debris, unknown, etc.) is defined in the
    vision agent's prompt, not hardcoded here, so new categories don't require
    a schema change. Kept as a distinct type only for readability at call sites.
    """


class DetectedSkyObject(BaseModel):
    """One object identified in a single day-sky frame.

    Strictly a passive detection/classification record -- this and everything
    downstream of it is early-warning/alerting only. Nothing in this codebase
    tracks, targets, or acts on a detected object beyond surfacing it to a
    human.
    """

    object_class: str = Field(description="e.g. bird, aircraft, drone, weather-balloon, debris, unknown")
    description: str = Field(description="Concrete visual description actually observed in the frame")
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box_pct: tuple[float, float, float, float] | None = Field(
        default=None, description="(x_min, y_min, x_max, y_max) as fraction of frame width/height, if localized"
    )
    anomaly: bool = Field(
        default=False, description="True only if this object doesn't match routine air traffic/wildlife/weather"
    )


class DaySkyAssessment(BaseModel):
    """Structured output of one day-sky frame analysis.

    Forced as a Gemini structured response; the rest of the pipeline treats
    this as data, matching InfrastructureRiskAssessment's pattern.
    """

    summary: str = Field(description="Plain-language summary of what's visible in the frame")
    weather_observations: list[str] = Field(default_factory=list)
    pollution_observations: list[str] = Field(default_factory=list)
    objects: list[DetectedSkyObject] = Field(default_factory=list)
    alert_level: str = Field(description="One of: none, watch, warning -- civil early-warning framing only")
    confidence_caveats: str = Field(
        description="What this assessment does NOT establish -- e.g. single-frame, no tracking, "
        "no identification of intent, classification only"
    )


class NightSkyReference(BaseModel):
    """One NASA GIBS VIIRS Day/Night Band tile reference for a region and date.

    This is metadata about a fetched tile, not the pixel data itself --
    callers fetch the actual image bytes from `tile_url` if needed.
    """

    date: str = Field(description="ISO date (YYYY-MM-DD) of the imagery")
    layer: str = Field(description="GIBS layer identifier used")
    lat: float
    lon: float
    tile_url: str
    cloud_cover_note: str | None = Field(
        default=None, description="Known limitation for this tile -- e.g. cloud cover obscuring surface detail"
    )


class CameraSource(BaseModel):
    """One configured camera/stream source, hardware-agnostic.

    `protocol` is deliberately restricted to open, cross-vendor standards
    (ONVIF for discovery/PTZ/profiles, plain RTSP as the universal fallback
    every IP camera supports) rather than any vendor SDK, so this never locks
    to one camera brand.
    """

    source_id: str
    protocol: str = Field(description="'onvif' or 'rtsp'")
    stream_url: str = Field(description="RTSP stream URL, either given directly or resolved via ONVIF")
    onvif_device_url: str | None = Field(default=None, description="ONVIF device service URL, if protocol='onvif'")
    label: str = Field(description="Human-readable location/purpose, e.g. 'Chennai rooftop, north-facing'")


class KnowledgeAssertion(BaseModel):
    """One entity-relation-entity fact extracted into the ontology store.

    Deliberately a flat triple, not a rich graph schema -- see
    docs/ARCHITECTURE.md for why a minimal representation was chosen over a
    full RDF/OWL ontology for this scope.
    """

    subject: str
    relation: str
    object: str
    source: str = Field(description="Where this fact came from -- a doc title, URL, or sensor reading")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    observed_at: datetime = Field(default_factory=lambda: datetime.now())


class RetrievedPassage(BaseModel):
    """One passage returned by the RAG retriever."""

    text: str
    source_title: str
    source_url: str | None = None
    score: float = Field(description="Similarity score, higher is more relevant")


class DataDomainRouting(BaseModel):
    """The router's judgment on which real data domains a query needs.

    Forced as a Gemini structured response. Deterministic Python then calls
    only the selected domains' real modules -- the model classifies, it does
    not itself fetch data.
    """

    domains: list[str] = Field(
        description="Subset of: weather, cyclone_track, night_sky, research -- "
        "only the domains actually needed to answer the query"
    )
    reasoning: str = Field(description="One sentence on why these domains were chosen")
