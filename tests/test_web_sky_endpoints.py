"""New sky/RAG/router endpoints on the FastAPI app, tested with the
underlying real-data functions mocked -- no live API keys or network calls."""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from coppernick.schema import DaySkyAssessment, DataDomainRouting
from coppernick.web import app

client = TestClient(app)


def test_sky_night_returns_tile_reference():
    response = client.get("/sky/night", params={"lat": 13.08, "lon": 80.27})
    assert response.status_code == 200
    body = response.json()
    assert body["layer"] == "VIIRS_NOAA21_DayNightBand"
    assert "tile_url" in body


def test_sky_day_scan_returns_assessment():
    fake_assessment = DaySkyAssessment(
        summary="Clear sky.",
        alert_level="none",
        confidence_caveats="Single-frame only.",
    )
    with patch("coppernick.web.build_vision_client", return_value=MagicMock()), \
         patch("coppernick.web.analyze_frame", return_value=fake_assessment):
        response = client.post(
            "/sky/day-scan",
            json={"image_base64": base64.b64encode(b"fake-image-bytes").decode("ascii")},
        )
    assert response.status_code == 200
    assert response.json()["alert_level"] == "none"


def test_research_index_and_query():
    with patch("coppernick.web.build_client", return_value=MagicMock()), \
         patch("coppernick.web.fetch_arxiv_abstracts", return_value=[{"title": "T", "summary": "S", "url": "http://x"}]), \
         patch("coppernick.web.index_documents", return_value=1):
        index_response = client.post("/research/index", params={"query": "cyclone risk"})
    assert index_response.status_code == 200
    assert index_response.json()["indexed"] == 1

    with patch("coppernick.web.build_client", return_value=MagicMock()), \
         patch("coppernick.web.retrieve", return_value=[]):
        query_response = client.get("/research", params={"query": "cyclone risk"})
    assert query_response.status_code == 200
    assert query_response.json() == {"results": []}


def test_route_query_dispatches_and_serializes():
    fake_decision = DataDomainRouting(domains=["weather"], reasoning="test")
    with patch("coppernick.web.build_client", return_value=MagicMock()), \
         patch("coppernick.web.router.classify_domains", return_value=fake_decision), \
         patch("coppernick.web.router.fetch_for_domains", return_value={"weather": {"lat": 13.08}}):
        response = client.get("/route", params={"query": "will it rain", "lat": 13.08, "lon": 80.27})
    assert response.status_code == 200
    body = response.json()
    assert body["domains"] == ["weather"]
    assert body["results"]["weather"] == {"lat": 13.08}
