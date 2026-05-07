# 🔭 Stargazer

A full-stack astronomy platform that ingests NASA's Astronomy Picture of the Day, uses an AI agent to identify and catalog celestial bodies, and lets you explore what's visible in the night sky from any address — with an interactive sky viewer powered by real telescope survey imagery.

Live: https://stargazer-production-d04d.up.railway.app

## Architecture

```
NASA APOD API → Django ingestion → Claude agent (tool use) → SIMBAD/JPL validation → PostgreSQL
                                                                                          ↓
                                       Aladin Lite sky viewer ← React frontend ← REST API
                                                                                          ↓
                                              Vellum Workflow (Astrid) ← execute_workflow()
                                                        ↓
                                          POST /api/tools/* (Railway) ← tool execution
```

**Backend:** Django + Django REST Framework + PostgreSQL (Railway)
**Frontend:** React + TypeScript + Vite + astronomy-engine + Aladin Lite
**Ingestion Agent:** Claude Haiku with agentic tool-use loop + 4-layer validation pipeline
**Conversational Layer:** Vellum ToolCallingNode workflow (`astrid-agent`) with 5 tools and full execution tracing

## How It Works

### The Ingestion Pipeline

`fetch_apod` pulls today's APOD from NASA's API. When a new entry lands, it triggers an **agentic Claude loop** that:

1. Reads the APOD title and explanation
2. Identifies the primary celestial body
3. Checks the database for duplicates via tool use
4. Saves the body with real RA/Dec coordinates
5. Links it to the APOD through a Collection join table

The agent uses two tools (`search_previous_apods`, `save_celestial_body`) and runs up to 8 turns with prompt caching enabled. All writes are idempotent via `get_or_create`.

### Coordinate Validation Pipeline

Every celestial body goes through a 4-layer validation pipeline before being saved:

1. **Claude extraction** — identifies the body and provides initial coordinates
2. **SIMBAD cross-reference** — validates against CDS Strasbourg's authoritative deep-sky database
3. **JPL Horizons fallback** — for solar system objects (planets, moons, comets, asteroids)
4. **Graceful degradation** — if neither source can verify, the body is accepted with an `unverified` flag rather than silently rejected

### The Data Model

- **Apod** — NASA APOD entries keyed on date (title, explanation, image URLs, media type)
- **CelestialBody** — Astronomy catalog (name, type, RA/Dec, description, verification status)
- **Collection** — Join table with `collected_at` timestamp (explicit model, not M2M, for metadata support)

### The Frontend

- **Aladin Lite Sky Viewer** — Interactive sky viewer from CDS (Strasbourg) embedded in React. Renders real telescope survey imagery (Digitized Sky Survey). Pans to any celestial body's RA/Dec coordinates when selected. Same organization that powers SIMBAD validation.
- **StarFinder** — Address input → Nominatim geocoding → real-time altitude/azimuth calculation via `astronomy-engine`. Shows what's visible tonight from any location with Bortle scale light pollution assessment.
- **Collection Grid** — Browse collected bodies with their linked APOD images

### Light Pollution: Bortle Scale

Visibility calculations include a Bortle class assessment for any location. A Bortle 8 (Brooklyn) shows 4 naked-eye objects while a Bortle 5 (Hudson, NY) shows 8 — same night, same sky, different experience. Equipment recommendations (naked eye, binoculars, telescope) adjust per location.

### The Conversational Layer (Astrid)

Astrid is a deployed Vellum workflow (`astrid-agent`) — a `ToolCallingNode` running claude-sonnet-4-6 with five tools. Django doesn't run the agent loop; it calls `client.execute_workflow()` and returns the result. Every conversation traces automatically in the Vellum dashboard: tool calls, model reasoning, latency, and cost.

The tool execution pattern: Vellum's hosted runner calls back to Django's `/api/tools/*` endpoints, which run the tool scripts as subprocesses on Railway and return results. Vellum handles the reasoning; Railway handles the execution.

| Tool | Purpose |
|---|---|
| `get_visible_tonight` | Address → geocode → visible bodies with altitude, compass direction, Bortle assessment |
| `get_todays_apod` | Today's NASA Astronomy Picture of the Day |
| `get_celestial_bodies` | Full Stargazer catalog |
| `lookup_simbad` | Deep-sky object lookup (stars, nebulae, galaxies) via CDS Strasbourg |
| `lookup_jpl_horizons` | Solar system ephemeris (planets, moons, comets) via NASA/JPL |

Astrid chains tools together. Ask "what's above me tonight?" and she'll check visibility, cross-reference with today's APOD, and connect them: *"The Pleiades are above you right now — and they're actually today's NASA picture of the day."*

### Observability

Each request generates a UUID (`external_id`) that is:
- Passed to `execute_workflow()` as the Vellum external ID
- Logged in Railway's structured log stream alongside the Vellum `execution_id`

This links Django logs to Vellum execution traces across two systems — searchable by either ID. The `trace_id` is also returned in the API response for frontend correlation.

Workflow deployment: https://app.vellum.ai/public/workflow-deployments/f0269cdb-6b46-4452-9c6f-bb776537b3ba?releaseTag=LATEST

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Vellum ToolCallingNode over hand-rolled agent loop | Execution tracing, cost visibility, and tool schema generation out of the box — no infrastructure to maintain |
| claude-sonnet-4-6 for Astrid (upgraded from Haiku) | Multi-tool chaining requires stronger reasoning; Sonnet's quality difference was immediately noticeable |
| Claude Haiku for ingestion agent | Structured extraction task, 10x cheaper, fast enough for tool use — model choice should match the job |
| Tools call back to Django via HTTP | Vellum's hosted runner can't exec subprocesses; Django is the execution environment, Vellum is the reasoning layer |
| Explicit Collection model over ManyToManyField | Needed `collected_at` metadata on the relationship |
| Bounded agent loop (8 turns max) | Prevents runaway API costs; agent must converge |
| Read-before-write via `get_or_create` | Idempotent writes prevent duplicate catalog entries |
| SIMBAD + JPL dual validation | Different authorities for different object types; graceful fallback |
| Fail-closed validation with `unverified` flag | Never silently wrong; surfaces uncertainty to the user |
| Client-side astronomy calculations | Zero server load, real-time updates, works offline after initial data fetch |
| Aladin Lite over custom WebGL | Real telescope imagery from CDS, battle-tested, same ecosystem as SIMBAD |
| Read-only API | Writes happen through management commands and the agent, clean separation |
| Nominatim over Google Geocoding | Free, no API key, sufficient accuracy for sky observation |
| stdlib urllib in tools.py | No third-party dependencies in Vellum's hosted execution environment |

## Setup

```bash
# Backend
cd stargazer
python -m venv venv
source venv/bin/activate
pip install django djangorestframework psycopg2-binary python-dotenv vellum-ai requests

# Create .env
echo "NASA_API_KEY=your_key_here" > .env
echo "VELLUM_API_KEY=your_key_here" >> .env
echo "STARGAZER_BASE_URL=http://localhost:8000" >> .env

# Database (PostgreSQL)
createdb stargazer
python manage.py migrate
python manage.py seed_bodies

# Fetch today's APOD + run agent
python manage.py fetch_apod

# Start backend
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Management Commands

| Command | Purpose |
|---|---|
| `python manage.py fetch_apod [date]` | Fetch a single APOD, run the agent on new entries |
| `python manage.py bulk_import_apods --start YYYY-MM-DD` | Backfill APODs from NASA (images only, no agent) |
| `python manage.py seed_bodies` | Seed 12 well-known celestial bodies |
| `python manage.py refresh_planet_coords` | Update RA/Dec for solar system bodies via JPL Horizons |

## Tech Stack

- Python 3.11 / Django 5.2 / DRF
- PostgreSQL (Railway)
- React 19 / TypeScript / Vite
- Aladin Lite v3 (CDS Strasbourg - interactive sky viewer)
- astronomy-engine (client-side celestial mechanics)
- Vellum (agent workflow orchestration, tracing, observability)
- claude-sonnet-4-6 via Vellum (conversational agent)
- Claude Haiku (APOD ingestion agent with prompt caching)
- SIMBAD (CDS Strasbourg - deep-sky object database)
- JPL Horizons (NASA/JPL - solar system ephemeris)
- Nominatim / OpenStreetMap (geocoding)
- NASA APOD API

---

Built by Sarah Kate · Brooklyn, NY
