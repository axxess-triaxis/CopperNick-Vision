"""Day-sky vision analysis: Gemini multimodal frame classification.

Strictly passive detection/classification for civil early-warning purposes --
weather, pollution, and aerial-object anomalies. This module never tracks,
targets, or acts on a detected object beyond returning a structured
assessment for a human to review; `alert_level` and `anomaly` flags are
informational, not triggers for any automated response.

API shape (client.interactions.create with a multimodal `input` list mixing
text and image parts, `response_format` with a JSON Schema) verified against
ai.google.dev/gemini-api/docs (checked 2026-09-17) -- the same Interactions
API surface already verified and used in agent.py.
"""

from __future__ import annotations

import base64
import os

from google import genai

from ..agent import GEMINI_CALL_TIMEOUT_SECONDS
from ..schema import DaySkyAssessment

SYSTEM_PROMPT = """You are CopperNick's Sky Watch vision module -- a passive, civilian \
early-warning classifier for a single day-sky camera frame. You NEVER track, target, or \
recommend action against any object; you only classify and describe what is visible, for a \
human reviewer.

For the frame you are given:
- weather_observations: concrete visual weather signals actually visible (cloud type/density, \
  haze, precipitation, visible smoke).
- pollution_observations: concrete visual signals of air quality (smog haze, visible \
  particulate, unusual sky discoloration) -- never invent a numeric AQI from a single image.
- objects: every distinct aerial object visible, each classified into a plain category \
  (bird, aircraft, drone, weather-balloon, kite, debris, unknown, etc.) with a concrete visual \
  description and a confidence score. Set anomaly=true ONLY for an object that doesn't match \
  routine air traffic, wildlife, or weather phenomena -- an unfamiliar shape, unusual flight \
  behavior, or something inconsistent with known local air traffic patterns. anomaly=true is \
  never a claim about intent or origin, only that it doesn't match routine categories.
- alert_level: 'none' for routine skies, 'watch' when something unusual but not urgent is \
  present, 'warning' only when there's a concrete, describable reason for immediate human \
  attention. This is an early-warning signal for a human to review, never an automated trigger.
- confidence_caveats: state plainly that this is a single-frame classification with no \
  tracking across frames, no radar/transponder correlation, and no determination of an \
  object's intent -- classification only."""


def build_vision_client() -> genai.Client:
    return genai.Client()


def analyze_frame(
    client: genai.Client,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    location_context: str | None = None,
) -> DaySkyAssessment:
    """Classify one day-sky camera frame. `image_bytes` is the raw frame data."""

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    parts = [{"type": "text", "text": SYSTEM_PROMPT}]
    if location_context:
        parts.append({"type": "text", "text": f"Camera location context: {location_context}"})
    parts.append({"type": "image", "data": image_b64, "mime_type": mime_type})

    interaction = client.interactions.create(
        model=os.environ.get("COPPERNICK_GEMINI_MODEL", "gemini-3.8-flash"),
        input=parts,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": DaySkyAssessment.model_json_schema(),
        },
        timeout=GEMINI_CALL_TIMEOUT_SECONDS,
    )
    return DaySkyAssessment.model_validate_json(interaction.output_text)
