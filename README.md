# 🔭 Stargazer

A full-stack astronomy platform that ingests NASA's Astronomy Picture of the Day, uses an AI agent to identify and catalog celestial bodies, and lets you explore what's visible in the night sky from any address — with an interactive sky viewer powered by real telescope survey imagery.

## Architecture

```
NASA APOD API → Django ingestion → Claude agent (tool use) → SIMBAD/JPL validation → PostgreSQL
                                                                                          ↓
                                       Aladin Lite sky viewer ← React frontend ← REST API → Vellum skill (Astrid)
```

**Backend:** Django + Django REST Framework + PostgreSQL
**Frontend:** React + TypeScript + Vite + astronomy-engine + Aladin Lite
**AI Agent:** Claude Haiku with agentic tool-use loop + 4-layer validation pipeline
**Skill Layer:** Vellum custom skill with multi-tool chaining and agentic reasoning

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

### The Vellum Skill (Astrid)

A custom Vellum assistant skill with agentic multi-tool chaining. Five tools:

| Tool | Purpose |
|---|---|
| `get_visible_tonight` | Address → geocode → visible bodies with altitude, compass direction, Bortle assessment |
| `get_todays_apod` | Today's NASA Astronomy Picture of the Day |
| `get_celestial_bodies` | Full Stargazer catalog |
| `lookup_simbad` | Deep-sky object validation (stars, nebulae, galaxies) via CDS |
| `lookup_jpl_horizons` | Solar system ephemeris (planets, moons, comets) via NASA/JPL |

Astrid doesn't just answer questions — she chains tools together. Ask "what's above me tonight?" and she'll check visibility, cross-reference with today's APOD, and connect them: *"The Pleiades are above you right now — and they're actually today's NASA picture of the day."*

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Explicit Collection model over ManyToManyField | Needed `collected_at` metadata on the relationship |
| Bounded agent loop (8 turns max) | Prevents runaway API costs; agent must converge |
| Read-before-write via `get_or_create` | Idempotent writes prevent duplicate catalog entries |
| SIMBAD + JPL dual validation | Different authorities for different object types; graceful fallback |
| Fail-closed validation with `unverified` flag | Never silently wrong; surfaces uncertainty to the user |
| Client-side astronomy calculations | Zero server load, real-time updates, works offline after initial data fetch |
| Aladin Lite over custom WebGL | Real telescope imagery from CDS, battle-tested, same ecosystem as SIMBAD |
| Read-only API | Writes happen through management commands and the agent, clean separation |
| Nominatim over Google Geocoding | Free, no API key, sufficient accuracy for sky observation |
| Haiku over Sonnet for the agent | Structured extraction task, 10x cheaper, fast enough for tool use |

## Setup

```bash
# Backend
cd stargazer
python -m venv venv
source venv/bin/activate
pip install django djangorestframework psycopg2-binary python-dotenv anthropic requests

# Create .env
echo "NASA_API_KEY=your_key_here" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

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

## Tech Stack

- Python 3.11 / Django 5.2 / DRF
- PostgreSQL
- React 19 / TypeScript / Vite
- Aladin Lite v3 (CDS Strasbourg - interactive sky viewer)
- astronomy-engine (client-side celestial mechanics)
- Claude Haiku (agentic tool use with prompt caching)
- SIMBAD (CDS Strasbourg - deep-sky object database)
- JPL Horizons (NASA/JPL - solar system ephemeris)
- Nominatim / OpenStreetMap (geocoding)
- NASA APOD API

---

Built by Sarah Kate · Brooklyn, NY
