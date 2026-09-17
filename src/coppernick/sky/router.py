"""LLM routing across CopperNick's real data domains: live weather, historical
cyclone tracks, NASA night-sky imagery, and the research RAG store.

Deliberately reuses the same structured-output pattern already verified in
agent.py and vision_detect.py rather than introducing Gemini's function-
calling/tools API as a second, unverified code path: the model classifies
which domains a query needs, then plain Python calls the corresponding real
module -- no domain is queried on the model's say-so alone, and every value
returned traces back to a real data source, not model invention.
"""

from __future__ import annotations

import os
from datetime import date

from google import genai

from ..data import ibtracs, open_meteo
from ..rag.retrieve import retrieve
from ..rag.store import VectorStore
from ..schema import DataDomainRouting
from . import night_sky

SYSTEM_PROMPT = """You classify which real data domains are needed to answer a query about \
weather, cyclones, night-sky imagery, or climate/disaster research. Choose only from: \
weather, cyclone_track, night_sky, research. Select every domain genuinely relevant -- do not \
default to all four, and do not select a domain the query doesn't call for."""

VALID_DOMAINS = {"weather", "cyclone_track", "night_sky", "research"}


def build_router_client() -> genai.Client:
    return genai.Client()


def classify_domains(client: genai.Client, query: str) -> DataDomainRouting:
    interaction = client.interactions.create(
        model=os.environ.get("COPPERNICK_GEMINI_MODEL", "gemini-3.8-flash"),
        input=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {"type": "text", "text": f"Query: {query}"},
        ],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": DataDomainRouting.model_json_schema(),
        },
    )
    decision = DataDomainRouting.model_validate_json(interaction.output_text)
    decision.domains = [d for d in decision.domains if d in VALID_DOMAINS]
    return decision


def fetch_for_domains(
    domains: list[str],
    lat: float,
    lon: float,
    research_query: str | None = None,
    ibtracs_df=None,
    storm_name: str | None = None,
    storm_season: int | None = None,
    rag_client: genai.Client | None = None,
    rag_store: VectorStore | None = None,
) -> dict:
    """Deterministically fetch real data for each selected domain.

    Every result here comes from a real module already verified elsewhere in
    this codebase (open_meteo, ibtracs, night_sky, rag.retrieve) -- this
    function is pure dispatch, it invents nothing.
    """

    results: dict = {}
    if "weather" in domains:
        results["weather"] = open_meteo.fetch_forecast(lat, lon)
    if "cyclone_track" in domains and ibtracs_df is not None and storm_name:
        results["cyclone_track"] = ibtracs.get_storm_track(ibtracs_df, storm_name, storm_season)
    if "night_sky" in domains:
        results["night_sky"] = night_sky.build_tile_url(lat, lon, on_date=date.today())
    if "research" in domains and research_query and rag_client and rag_store is not None:
        results["research"] = retrieve(rag_client, rag_store, research_query)
    return results
