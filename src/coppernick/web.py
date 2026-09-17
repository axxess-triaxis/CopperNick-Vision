"""FastAPI app wiring data loaders to the agent.

This satisfies the hackathon's "deployed link" requirement -- deployed and
public at https://coppernick-222356459208.asia-south1.run.app (see README
Status for exactly what is and isn't wired up on the live service).
"""

from __future__ import annotations

import base64
import os
from datetime import date

from fastapi import FastAPI
from pydantic import BaseModel

from .agent import assess_risk, build_client
from .data import earth_engine, ibtracs, open_meteo
from .rag.retrieve import index_documents, retrieve
from .rag.store import VectorStore
from .rag.corpus import fetch_arxiv_abstracts
from .sky import night_sky, router
from .sky.vision_detect import analyze_frame, build_vision_client

app = FastAPI(title="CopperNick")
_client = None
_tracks_df = None
_rag_store: VectorStore | None = None


def _get_client():
    global _client
    if _client is None:
        _client = build_client()
    return _client


def _get_tracks_df():
    global _tracks_df
    if _tracks_df is None:
        _tracks_df = ibtracs.load_ni_basin_tracks()
    return _tracks_df


def _get_rag_store() -> VectorStore:
    global _rag_store
    if _rag_store is None:
        _rag_store = VectorStore()
    return _rag_store


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/assess/{storm_name}")
def assess(storm_name: str, season: int, lat: float, lon: float) -> dict:
    """Assess risk for a named historical storm, using current live weather
    at the given coordinates as the "what if this happened again now" signal.
    """

    track = ibtracs.get_storm_track(_get_tracks_df(), storm_name, season)
    weather = open_meteo.fetch_forecast(lat, lon)

    gee_project = os.environ.get("GEE_PROJECT_ID")
    image_count = 0
    if gee_project:
        earth_engine.ensure_initialized(gee_project)
        start = weather.hourly_times[0].date().isoformat()
        end = weather.hourly_times[-1].date().isoformat()
        image_count = earth_engine.fetch_recent_imagery_count(lat, lon, start, end)

    assessment = assess_risk(_get_client(), track, weather, image_count)
    return assessment.model_dump()


@app.get("/sky/night")
def sky_night(lat: float, lon: float) -> dict:
    """Resolve a NASA GIBS night-sky tile reference for the given coordinate.

    Does not download or process the tile's pixel data -- returns the
    verified-real tile URL for the caller to fetch/display.
    """

    return night_sky.build_tile_url(lat, lon).model_dump()


class DaySkyScanRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"
    location_context: str | None = None


@app.post("/sky/day-scan")
def sky_day_scan(body: DaySkyScanRequest) -> dict:
    """Classify a single day-sky camera frame. Passive detection/alerting
    only -- see sky/vision_detect.py's module docstring for the explicit
    scope boundary.
    """

    image_bytes = base64.b64decode(body.image_base64)
    assessment = analyze_frame(
        build_vision_client(), image_bytes, mime_type=body.mime_type, location_context=body.location_context
    )
    return assessment.model_dump()


@app.post("/research/index")
def research_index(query: str, max_results: int = 10) -> dict:
    """Fetch and index arXiv abstracts for a topic into the in-memory RAG store."""

    papers = fetch_arxiv_abstracts(query, max_results=max_results)
    count = index_documents(_get_client(), _get_rag_store(), papers)
    return {"indexed": count, "store_size": len(_get_rag_store())}


@app.get("/research")
def research_query(query: str, top_k: int = 5) -> dict:
    """Retrieve the most relevant passages already indexed via /research/index."""

    passages = retrieve(_get_client(), _get_rag_store(), query, top_k=top_k)
    return {"results": [p.model_dump() for p in passages]}


@app.get("/route")
def route_query(query: str, lat: float, lon: float, storm_name: str | None = None, season: int | None = None) -> dict:
    """LLM-classify which real data domains a query needs, then dispatch to
    only those real modules -- see sky/router.py's module docstring."""

    decision = router.classify_domains(_get_client(), query)
    results = router.fetch_for_domains(
        decision.domains,
        lat,
        lon,
        research_query=query,
        ibtracs_df=_get_tracks_df() if "cyclone_track" in decision.domains else None,
        storm_name=storm_name,
        storm_season=season,
        rag_client=_get_client(),
        rag_store=_get_rag_store(),
    )
    serialized = {
        k: (v.model_dump() if hasattr(v, "model_dump") else [p.model_dump() for p in v] if isinstance(v, list) else v)
        for k, v in results.items()
    }
    return {"domains": decision.domains, "reasoning": decision.reasoning, "results": serialized}
