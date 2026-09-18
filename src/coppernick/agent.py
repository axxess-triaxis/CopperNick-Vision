"""Gemini Interactions API agent: reasons over track/weather/imagery signals
to produce one InfrastructureRiskAssessment.

API shape (client.interactions.create, response_format with a JSON Schema)
verified against ai.google.dev/gemini-api/docs/structured-output (checked
2026-09-17).
"""

from __future__ import annotations

import os

from google import genai

from .schema import CycloneTrackPoint, InfrastructureRiskAssessment, WeatherSnapshot

# A live production request hung well past 90s with no timeout set (the SDK
# accepts `timeout: float | httpx.Timeout | None`, confirmed by introspecting
# the installed client -- default is None, i.e. unbounded) when Gemini
# returned a 429 rate-limit and the client's own retry behavior didn't fail
# fast. A bounded timeout turns a multi-minute hang into a clear, fast error.
GEMINI_CALL_TIMEOUT_SECONDS = 45.0

SYSTEM_PROMPT = """You are CopperNick, an early-warning risk assessment agent for cyclone \
impact on infrastructure in the Bay of Bengal / coastal India region.

You are handed a historical cyclone track (from IBTrACS), a live weather forecast for the \
region (from Open-Meteo), and a satellite image count for the area (from Google Earth Engine, \
as a rough signal of imagery coverage available for the affected area -- not an infrastructure \
inventory). Produce a plain-language risk assessment for local municipal and disaster \
management authorities.

Be concrete: reference the actual wind speeds, pressure readings, and precipitation forecasts \
handed to you rather than describing risk in the abstract. Be explicit in confidence_caveats \
about what this assessment does NOT include -- there is no physical storm-surge simulation \
here, no verified infrastructure inventory, and no ground-truth validation of this specific \
event. This is a decision-support draft, not a certified forecast."""


def build_client() -> genai.Client:
    return genai.Client()


def assess_risk(
    client: genai.Client,
    track: list[CycloneTrackPoint],
    weather: WeatherSnapshot,
    satellite_image_count: int,
) -> InfrastructureRiskAssessment:
    track_summary = "\n".join(
        f"{p.timestamp.isoformat()}: lat={p.lat}, lon={p.lon}, "
        f"wind={p.wind_knots} kt, pressure={p.pressure_mb} mb"
        for p in track
    )
    prompt = (
        f"Cyclone track ({track[0].name if track else 'unknown'}):\n{track_summary}\n\n"
        f"Live forecast at ({weather.lat}, {weather.lon}):\n"
        f"Hourly precipitation (mm): {weather.hourly_precipitation_mm}\n"
        f"Hourly wind speed (km/h): {weather.hourly_wind_speed_kmh}\n\n"
        f"Satellite images available for the area/period: {satellite_image_count}"
    )

    interaction = client.interactions.create(
        model=os.environ.get("COPPERNICK_GEMINI_MODEL", "gemini-3.8-flash"),
        input=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {"type": "text", "text": prompt},
        ],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": InfrastructureRiskAssessment.model_json_schema(),
        },
        timeout=GEMINI_CALL_TIMEOUT_SECONDS,
    )
    return InfrastructureRiskAssessment.model_validate_json(interaction.output_text)
