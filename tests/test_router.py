"""LLM domain router, tested with the genai client and data modules mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from coppernick.schema import DataDomainRouting
from coppernick.sky.router import classify_domains, fetch_for_domains


def test_classify_domains_filters_invalid_domains():
    mock_client = MagicMock()
    decision_json = DataDomainRouting(
        domains=["weather", "not_a_real_domain", "research"], reasoning="test"
    ).model_dump_json()
    mock_client.interactions.create.return_value = MagicMock(output_text=decision_json)

    result = classify_domains(mock_client, "will it rain near Chennai and what does research say?")

    assert result.domains == ["weather", "research"]


def test_fetch_for_domains_calls_only_selected_domains():
    with patch("coppernick.sky.router.open_meteo.fetch_forecast", return_value="WEATHER") as mock_weather, \
         patch("coppernick.sky.router.night_sky.build_tile_url", return_value="NIGHT") as mock_night:
        results = fetch_for_domains(domains=["weather", "night_sky"], lat=13.08, lon=80.27)

    assert results == {"weather": "WEATHER", "night_sky": "NIGHT"}
    mock_weather.assert_called_once()
    mock_night.assert_called_once()


def test_fetch_for_domains_skips_cyclone_track_without_data():
    results = fetch_for_domains(domains=["cyclone_track"], lat=0, lon=0)
    assert "cyclone_track" not in results


def test_fetch_for_domains_empty_domains_returns_empty():
    results = fetch_for_domains(domains=[], lat=0, lon=0)
    assert results == {}
