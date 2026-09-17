# CopperNick

An AI-native sky/atmosphere patrolling observer — a cyclone impact and
infrastructure vulnerability forecaster, built for
**[Build with AI: Code for Communities](https://hack2skill.com/event/codeforcommunities2)**
(hack2skill / Google Cloud, Track 05, deadline **2026-09-30**), and
positioned as a submission candidate for **GOSIM Shenzhen 2026**'s Spotlight
open call / OAIC Agentic Factory Hackathon (registration not yet open there).

## Concept

Track 05's brief: build an AI-powered predictive risk and vulnerability
modeling platform that simulates cyclone storm surges, predicts local
rainfall damage pathways, maps exposure for critical infrastructure (power
grids, arterial roads, medical shelters), and automates early-warning
advisory dispatches for municipal and disaster management authorities in
the Bay of Bengal / coastal APAC region.

CopperNick combines three real, independently-sourced signals into one
Gemini-reasoned risk assessment:

1. **Historical cyclone tracks** — NOAA's IBTrACS North Indian Ocean basin
   dataset (real storm tracks, wind, and pressure records covering the Bay
   of Bengal, including India's own RSMC New Delhi agency data).
2. **Live meteorological data** — Open-Meteo's free forecast API (rainfall,
   wind speed) for the region being assessed.
3. **Satellite imagery** — Google Earth Engine, for the infrastructure
   exposure layer (what's actually in the storm's projected path).

Gemini (via the Interactions API) reasons over all three to produce a
plain-language risk assessment and a draft early-warning advisory —
Gemini does the judgment, the rest of the pipeline stays deterministic.

## Sky Watch — passive early-warning scanning

A second subsystem, strictly civilian early-warning/alerting only — no
tracking, targeting, or engagement capability of any kind, by design:

1. **Day-sky vision** ([`sky/vision_detect.py`](src/coppernick/sky/vision_detect.py)) —
   Gemini multimodal classification of a single camera frame for weather,
   pollution, and aerial-object anomalies (birds, aircraft, drones, debris,
   etc.). Classification only — no cross-frame tracking, no determination of
   intent.
2. **Night-sky cross-referencing** ([`sky/night_sky.py`](src/coppernick/sky/night_sky.py)) —
   explicitly *not* vision-dependent: resolves real NASA GIBS VIIRS Day/Night
   Band tile URLs (`VIIRS_NOAA21_DayNightBand`, verified live, checked
   2026-09-17) for a coordinate and date.
3. **Hardware-agnostic camera ingestion** ([`sky/camera_ingest.py`](src/coppernick/sky/camera_ingest.py)) —
   ONVIF (the cross-vendor IP-camera standard) for discovery and stream
   resolution, plain RTSP as the universal fallback every camera brand
   supports. **Hardware-unverified**: no physical camera exists in this
   development environment — the code is correct against the real installed
   library APIs, not tested against real hardware.
4. **LLM routing across real data domains** ([`sky/router.py`](src/coppernick/sky/router.py)) —
   Gemini classifies which of weather / cyclone-track / night-sky / research
   a query needs; plain Python then calls only those real modules. The model
   never fetches data itself.
5. **RAG over public research** ([`rag/`](src/coppernick/rag)) — arXiv's real
   public API (climate/disaster-response papers) embedded via
   `gemini-embedding-001` into an in-memory vector store. Public,
   unclassified sources only.
6. **Ontology/memory store** ([`sky/ontology.py`](src/coppernick/sky/ontology.py)) —
   a flat subject-relation-object triple store, Gemini-extracted from
   observations/research text, JSON-file-persistable. Deliberately not a
   full RDF/OWL reasoner — see docs/ARCHITECTURE.md for why.

## Status

Early scaffold, built fresh for this hackathon (no code shared with any
other project in this account). What exists right now:

- Pydantic schemas for cyclone track points, weather snapshots, and risk
  assessments ([`schema.py`](src/coppernick/schema.py))
- A real, verified IBTrACS loader for the North Indian basin CSV
  ([`data/ibtracs.py`](src/coppernick/data/ibtracs.py))
- A real Open-Meteo client, no API key required
  ([`data/open_meteo.py`](src/coppernick/data/open_meteo.py))
- A Google Earth Engine wrapper for satellite imagery
  ([`data/earth_engine.py`](src/coppernick/data/earth_engine.py))
- A Gemini Interactions API agent that reasons over all three
  ([`agent.py`](src/coppernick/agent.py))
- A FastAPI app wiring the above together ([`web.py`](src/coppernick/web.py))
- Mocked unit tests for the data loaders and the agent
- **Deployed to Cloud Run and public**: https://coppernick-222356459208.asia-south1.run.app
  (project `project-16c62420-db89-448a-bab`, region `asia-south1`) — `GET
  /health` returns `200 {"status":"ok"}` with no auth required. This is the
  hackathon's "deployed link" requirement.
- **Earth Engine is live and verified**: real credentials authenticated, real
  Sentinel-2 queries confirmed working through `fetch_recent_imagery_count`
  against real coordinates.
- **Sky Watch subsystem scaffolded** (see above): 45/45 tests passing across
  night-sky, camera ingestion, day-sky vision, RAG, router, and ontology
  modules — all with mocked externals (no live camera, no live Gemini calls
  yet run end-to-end, since Gemini itself is still billing-blocked, see below).

**Not yet done** — stated plainly rather than implied otherwise:
- **Gemini API calls are blocked**: the API key is valid and every code path
  is verified correct against real API shapes, but every real call currently
  fails with `429: Your prepayment credits are depleted` — an AI Studio
  billing/identity-verification issue on the account, separate from standard
  GCP project billing (which is fine — Earth Engine and Cloud Run both work).
  This blocks live end-to-end testing of every Gemini-dependent path: risk
  assessment, day-sky vision, embeddings, routing, and ontology extraction.
- No storm surge or rainfall damage *simulation* exists yet (only data
  ingestion + Gemini's own reasoning, not a physical model).
- **Camera ingestion is hardware-unverified** — correct against the real
  ONVIF/RTSP library APIs, never exercised against a physical camera.
- The live Cloud Run service has **not** been updated with the new Sky Watch
  endpoints yet — only the original `/assess` endpoint has been deployed and
  its env vars pushed; `/sky/*`, `/research/*`, and `/route` exist in the
  codebase but are not yet live.
- The RAG store is in-memory only (resets on every server restart) and needs
  explicit `/research/index` calls before `/research` returns anything.
- None of the hackathon's non-code deliverables (demo video, pitch deck) exist
  yet.

## Tools used

| Purpose | Service | Package | Verified against |
|---|---|---|---|
| AI reasoning | Gemini API (Interactions) | `google-genai` | ai.google.dev/gemini-api/docs |
| Satellite imagery | Google Earth Engine | `ee` | developers.google.com/earth-engine |
| Historical cyclone tracks | NOAA IBTrACS (North Indian basin) | `pandas` (CSV) | ncei.noaa.gov IBTrACS v04r01 |
| Live weather | Open-Meteo | `httpx` | open-meteo.com/en/docs |
| Night-sky imagery | NASA GIBS (VIIRS Day/Night Band) | `httpx` (tile URL only) | gibs.earthdata.nasa.gov, verified via live GetCapabilities |
| Camera ingestion | ONVIF / RTSP | `onvif-zeep-async`, `wsdiscovery` | introspected from installed package APIs |
| Text embeddings | Gemini (`gemini-embedding-001`) | `google-genai` | ai.google.dev/gemini-api/docs/embeddings + SDK introspection |
| Research corpus | arXiv public API | `httpx` | export.arxiv.org, verified live |

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env  # fill in GEMINI_API_KEY and a GEE project ID
pytest
```

## License

MIT — see [LICENSE](LICENSE).
