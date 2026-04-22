# 🔭 Stargazer

A full-stack astronomy platform that ingests NASA's Astronomy Picture of the Day, uses an AI agent to identify and catalog celestial bodies, and lets you explore what's visible in the night sky from any address.

## Architecture

```
NASA APOD API → Django ingestion → Claude agent (tool use) → PostgreSQL
                                                                  ↓
                                              React frontend ← REST API → Vellum skill
```

**Backend:** Django + Django REST Framework + PostgreSQL
**Frontend:** React + TypeScript + Vite + astronomy-engine
**AI Agent:** Claude Haiku with agentic tool-use loop
**Skill Layer:** Vellum custom skill with address geocoding

## How It Works

### The Ingestion Pipeline

`fetch_apod` pulls today's APOD from NASA's API. When a new entry lands, it triggers an **agentic Claude loop** that:

1. Reads the APOD title and explanation
2. Identifies the primary celestial body
3. Checks the database for duplicates via tool use
4. Saves the body with real RA/Dec coordinates (provided by Claude's astronomy knowledge)
5. Links it to the APOD through a Collection join table

The agent uses two tools (`search_previous_apods`, `save_celestial_body`) and runs up to 8 turns with prompt caching enabled. All writes are idempotent via `get_or_create`.

### The Data Model

- **Apod** - NASA APOD entries keyed on date (title, explanation, image URLs, media type)
- **CelestialBody** - Astronomy catalog (name, type, RA/Dec, description)
- **Collection** - Join table with `collected_at` timestamp (explicit model, not M2M, for metadata support)

### The Frontend

- **SkyMap** - SVG equatorial coordinate map with RA/Dec grid, glowing body markers, and a background star field
- **StarFinder** - Address input → Nominatim geocoding → real-time altitude/azimuth calculation via `astronomy-engine`. Shows what's visible tonight from any location
- **Collection Grid** - Browse collected bodies with their linked APOD images

### The Vellum Skill

A custom Vellum assistant skill that exposes three tools:
- `get_visible_tonight` - accepts an address or lat/lon, geocodes it, and returns visible bodies with altitude and compass direction
- `get_todays_apod` - fetches today's Astronomy Picture of the Day
- `get_celestial_bodies` - returns the full catalog

This turns a database query into a conversational experience: *"What's in the sky tonight from 169 Madison Ave?"*

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Explicit Collection model over ManyToManyField | Needed `collected_at` metadata on the relationship |
| Claude provides RA/Dec, no lookup table | Generalizes to any celestial object without maintaining a dictionary |
| Haiku over Sonnet for the agent | Structured extraction task, 10x cheaper, fast enough for tool use |
| Client-side astronomy calculations | Zero server load, real-time updates, works offline after initial data fetch |
| Read-only API | Writes happen through management commands and the agent, clean separation of concerns |
| Nominatim over Google Geocoding | Free, no API key, sufficient accuracy for sky observation |

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
- astronomy-engine (client-side celestial mechanics)
- Claude Haiku (agentic tool use with prompt caching)
- Nominatim / OpenStreetMap (geocoding)
- NASA APOD API

---

Built by Sarah Kate · Brooklyn, NY
