"""Day-sky vision module, tested with the genai client mocked -- no real API
key, network call, or camera frame needed."""

from __future__ import annotations

from unittest.mock import MagicMock

from coppernick.schema import DaySkyAssessment, DetectedSkyObject
from coppernick.sky.vision_detect import analyze_frame


def _sample_assessment_json() -> str:
    return DaySkyAssessment(
        summary="Clear sky with one small aircraft visible, no anomalies.",
        weather_observations=["Clear sky, no visible cloud cover"],
        pollution_observations=["No visible haze"],
        objects=[
            DetectedSkyObject(
                object_class="aircraft",
                description="Small fixed-wing aircraft, high altitude, contrail visible",
                confidence=0.87,
                bounding_box_pct=(0.4, 0.1, 0.45, 0.13),
                anomaly=False,
            )
        ],
        alert_level="none",
        confidence_caveats="Single-frame classification only, no tracking or intent determination.",
    ).model_dump_json()


def test_analyze_frame_parses_structured_response():
    mock_client = MagicMock()
    mock_client.interactions.create.return_value = MagicMock(output_text=_sample_assessment_json())

    result = analyze_frame(mock_client, image_bytes=b"fake-jpeg-bytes", location_context="Chennai rooftop, north-facing")

    assert result.alert_level == "none"
    assert len(result.objects) == 1
    assert result.objects[0].object_class == "aircraft"
    assert result.objects[0].anomaly is False

    call_kwargs = mock_client.interactions.create.call_args.kwargs
    assert call_kwargs["response_format"]["mime_type"] == "application/json"
    image_parts = [p for p in call_kwargs["input"] if p.get("type") == "image"]
    assert len(image_parts) == 1
    assert image_parts[0]["mime_type"] == "image/jpeg"


def test_analyze_frame_without_location_context():
    mock_client = MagicMock()
    mock_client.interactions.create.return_value = MagicMock(output_text=_sample_assessment_json())

    analyze_frame(mock_client, image_bytes=b"fake-jpeg-bytes")

    call_kwargs = mock_client.interactions.create.call_args.kwargs
    text_parts = [p["text"] for p in call_kwargs["input"] if p.get("type") == "text"]
    assert not any("Camera location context" in t for t in text_parts)
