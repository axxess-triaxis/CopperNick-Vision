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

**Not yet done** — stated plainly rather than implied otherwise: no Google
Cloud project has been wired up with real credentials from this codebase,
Earth Engine access has not been requested/approved for this project, no
storm surge or rainfall damage *simulation* exists yet (only data
ingestion + Gemini's own reasoning, not a physical model), nothing is
deployed, and none of the hackathon's non-code deliverables (demo video,
pitch deck, deployed link) exist yet.

## Tools used

| Purpose | Service | Package | Verified against |
|---|---|---|---|
| AI reasoning | Gemini API (Interactions) | `google-genai` | ai.google.dev/gemini-api/docs |
| Satellite imagery | Google Earth Engine | `ee` | developers.google.com/earth-engine |
| Historical cyclone tracks | NOAA IBTrACS (North Indian basin) | `pandas` (CSV) | ncei.noaa.gov IBTrACS v04r01 |
| Live weather | Open-Meteo | `httpx` | open-meteo.com/en/docs |

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env  # fill in GEMINI_API_KEY and a GEE project ID
pytest
```

## License

MIT — see [LICENSE](LICENSE).
