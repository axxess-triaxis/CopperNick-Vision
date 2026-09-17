"""FastAPI app wiring data loaders to the agent.

This satisfies the hackathon's "deployed link" requirement once hosted --
not yet deployed anywhere (see README Status).
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from .agent import assess_risk, build_client
from .data import earth_engine, ibtracs, open_meteo

app = FastAPI(title="CopperNick")
_client = None
_tracks_df = None


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
