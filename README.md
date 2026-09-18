# CopperNick Vision

An AI-native cyclone impact and infrastructure vulnerability forecaster,
paired with a passive sky-scanning early-warning subsystem. Built for
**[Build with AI: Code for Communities](https://hack2skill.com/event/codeforcommunities2)**
(hack2skill / Google Cloud, Track 05, deadline **2026-09-30**).

**Live**: https://coppernick-222356459208.asia-south1.run.app

## About the name and GOSIM

This started as "CopperNick," scoped from a one-line brief ("a sky patrolling
agent observer, Gosim (China) Vision OS hackathon") before any of GOSIM's
actual event pages were checked. Once verified, **GOSIM Shenzhen 2026 has no
"Vision OS" hackathon or track** — the real hackathon-shaped events there are
Spotlight Shenzhen 2026 (an open call for AI-native products) and the OAIC
Agentic Factory Hackathon (registration not yet open, as of this writing).
"CopperNick Vision" is the current name, reflecting the vision/sky-scanning
capability actually built — not a claim of GOSIM eligibility, which remains
unconfirmed and secondary to the hack2skill submission this repo is actually
built for.

## Concept

Track 05's brief: build an AI-powered predictive risk and vulnerability
modeling platform that simulates cyclone storm surges, predicts local
rainfall damage pathways, maps exposure for critical infrastructure (power
grids, arterial roads, medical shelters), and automates early-warning
advisory dispatches for municipal and disaster management authorities in
the Bay of Bengal / coastal APAC region.

The repo has two subsystems: the **cyclone/infrastructure forecaster** (the
original Track 05 submission) and **Sky Watch** (a later addition, passive
early-warning sky-scanning). Both are real, tested code — see Status below
for exactly what has and hasn't been verified live.

### Cyclone/infrastructure forecaster

Combines three real, independently-sourced signals into one Gemini-reasoned
risk assessment:

1. **Historical cyclone tracks** — NOAA's IBTrACS North Indian Ocean basin
   dataset (real storm tracks, wind, and pressure records covering the Bay
   of Bengal, including India's own RSMC New Delhi agency data).
2. **Live meteorological data** — Open-Meteo's free forecast API (rainfall,
   wind speed) for the region being assessed.
3. **Satellite imagery** — Google Earth Engine, for the infrastructure
   exposure layer (what's actually in the storm's projected path).

Gemini (via the Interactions API) reasons over all three to produce a
plain-language risk assessment and a draft early-warning advisory — Gemini
does the judgment, the rest of the pipeline stays deterministic.

### Sky Watch — passive early-warning scanning

Strictly civilian early-warning/alerting only — **no tracking, targeting, or
engagement capability of any kind, by design.** `alert_level` and `anomaly`
fields are informational flags for a human reviewer; nothing in this codebase
acts on them automatically.

1. **Day-sky vision** ([`sky/vision_detect.py`](src/coppernick/sky/vision_detect.py)) —
   Gemini multimodal classification of a single camera frame for weather,
   pollution, and aerial-object anomalies (birds, aircraft, drones, debris,
   etc.). Classification only — no cross-frame tracking, no determination of
   intent.
2. **Night-sky cross-referencing** ([`sky/night_sky.py`](src/coppernick/sky/night_sky.py)) —
   explicitly *not* vision-dependent: resolves real NASA GIBS VIIRS Day/Night
   Band tile URLs (`VIIRS_NOAA21_DayNightBand`) for a coordinate and date.
3. **Hardware-agnostic camera ingestion** ([`sky/camera_ingest.py`](src/coppernick/sky/camera_ingest.py)) —
   ONVIF (the cross-vendor IP-camera standard) for discovery and stream
   resolution, plain RTSP as the universal fallback every camera brand
   supports. **Hardware-unverified** — see Status.
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
   full RDF/OWL reasoner — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
   for why.

## Status

Verified as of 2026-09-18. Read this section literally — it distinguishes
"code exists and is tested against mocks," "verified against real external
APIs," and "confirmed working live," which are three different claims.

**Confirmed working live, right now:**
- `GET /health` → `200 {"status":"ok"}`, no auth required.
- `GET /sky/night?lat=..&lon=..` → a real NASA GIBS tile URL, confirmed via
  a live request against the deployed service (not just local tests).
- **`GET /assess/{storm_name}` → a real, successful, end-to-end Gemini-powered
  risk assessment.** Confirmed live against `AMPHAN`/season 2020 at (13.08,
  80.27): correct `InfrastructureRiskAssessment` JSON, reasoning that
  correctly referenced AMPHAN's real historical peak intensity (145 kt) and
  the actual live Open-Meteo forecast at the queried coordinates, and an
  honest `confidence_caveats` field noting zero satellite imagery scenes were
  available. This is the first real Gemini call to ever complete successfully
  in this build — the AI Studio billing block (see below) was resolved by
  using a separate, unbilled AI Studio project instead of the original
  paid/prepay-blocked one.
  **Known issue**: this call took 2m41s — likely the ~28MB IBTrACS CSV being
  re-downloaded on a cold container start, not yet optimized. Fine for a demo
  video with a pre-warmed instance, not fine for a judge hitting it cold.
- Earth Engine: real credentials authenticated locally, real Sentinel-2
  queries confirmed against real coordinates through
  `fetch_recent_imagery_count` (locally — not yet wired into the live Cloud
  Run service, which is why the live `/assess` call above reported zero
  imagery scenes).
- IBTrACS and Open-Meteo: no auth needed, work as documented. One real bug
  fixed in this pass: IBTrACS uses a whitespace-only string as a missing-value
  marker in some cells, which crashed `/assess` with a 500 until fixed (see
  git history) — caught by this very live test, not by local tests alone.

**Code exists, tests pass (47/47 locally as of the last full run), not yet
exercised live:**
- `/sky/day-scan` (day-sky vision classification)
- `/research/index` and `/research` (RAG indexing/retrieval)
- `/route` (LLM domain routing)
- These are Gemini-dependent but structurally identical in pattern to
  `/assess`, which now works live — high confidence they'll work once
  exercised, but "high confidence" is not "confirmed," so they stay in this
  section until actually tested live.

**Explicitly not done:**
- No physical storm-surge or rainfall-damage *simulation* — only data
  ingestion + Gemini's own reasoning, not a physical model.
- **Camera ingestion is hardware-unverified** — correct against the real
  ONVIF/RTSP library APIs (confirmed by introspecting the installed
  packages), never exercised against a physical camera, since none exists
  in this development environment.
- The RAG store is in-memory only (resets on every server restart) and
  needs an explicit `/research/index` call before `/research` returns
  anything.
- No demo video or pitch deck — non-code hackathon deliverables, not
  started.
- No AWS/GCP-style Partner registration or eligibility gate applies here
  (unlike this account's other hackathon repo, Omnidamus) — hack2skill has
  no equivalent partner-program requirement as of the rules checked.

## Tools used

| Purpose | Service | Package | Verified against |
|---|---|---|---|
| AI reasoning | Gemini API (Interactions) | `google-genai` | ai.google.dev/gemini-api/docs |
| Satellite imagery | Google Earth Engine | `ee` | developers.google.com/earth-engine |
| Historical cyclone tracks | NOAA IBTrACS (North Indian basin) | `pandas` (CSV) | ncei.noaa.gov IBTrACS v04r01 |
| Live weather | Open-Meteo | `httpx` | open-meteo.com/en/docs |
| Night-sky imagery | NASA GIBS (VIIRS Day/Night Band) | `httpx` (tile URL only) | gibs.earthdata.nasa.gov, verified via live GetCapabilities and a live tile request |
| Camera ingestion | ONVIF / RTSP | `onvif-zeep-async`, `wsdiscovery` | introspected from installed package APIs |
| Text embeddings | Gemini (`gemini-embedding-001`) | `google-genai` | ai.google.dev/gemini-api/docs/embeddings + SDK introspection |
| Research corpus | arXiv public API | `httpx` | export.arxiv.org, verified live |
| Deployment | Google Cloud Run | `gcloud` | project `project-16c62420-db89-448a-bab`, region `asia-south1` |

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env  # fill in GEMINI_API_KEY and a GEE project ID
pytest
```

## License

MIT — see [LICENSE](LICENSE).
