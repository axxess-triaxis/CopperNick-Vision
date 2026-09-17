"""Agent, tested with the genai client mocked -- no real API key or network
call needed."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from coppernick.agent import assess_risk
from coppernick.schema import CycloneTrackPoint, InfrastructureRiskAssessment, WeatherSnapshot


def _sample_assessment_json() -> str:
    return InfrastructureRiskAssessment(
        summary="High wind and heavy rainfall expected along the coastal path.",
        risk_level="high",
        likely_impacts=["Power grid outages", "Road flooding near the coast"],
        advisory_text="Evacuate low-lying coastal areas within 24 hours.",
        confidence_caveats="No physical storm-surge simulation; historical-track-based only.",
    ).model_dump_json()


def test_assess_risk_parses_structured_response():
    mock_client = MagicMock()
    mock_client.interactions.create.return_value = MagicMock(output_text=_sample_assessment_json())

    track = [
        CycloneTrackPoint(
            storm_id="s1", name="AMPHAN", timestamp=datetime(2026, 5, 16), lat=10.5, lon=80.1,
            wind_knots=60, pressure_mb=985,
        )
    ]
    weather = WeatherSnapshot(
        lat=10.5, lon=80.1,
        hourly_precipitation_mm=[5.0], hourly_wind_speed_kmh=[40.0],
        hourly_times=[datetime(2026, 9, 17)],
    )

    result = assess_risk(mock_client, track, weather, satellite_image_count=3)

    assert result.risk_level == "high"
    assert "Evacuate" in result.advisory_text
    mock_client.interactions.create.assert_called_once()
    call_kwargs = mock_client.interactions.create.call_args.kwargs
    assert call_kwargs["response_format"]["mime_type"] == "application/json"
