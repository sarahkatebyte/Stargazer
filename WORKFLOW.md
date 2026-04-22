# Stargazer Build Workflow

A running log of everything we've built, in order. Use this to retrace steps or explain the project in an interview.

---

## Phase 1 — Django Backend

### 1. Project setup
- Created virtual environment (`venv`) and activated it
- Installed Django, DRF, psycopg2, python-dotenv, anthropic, requests
- Created Django project (`stargazer`) and app (`apod`)
- Connected to a PostgreSQL database via `settings.py`

### 2. Defined models (`apod/models.py`)
- `Apod` — stores NASA APOD data: date, title, explanation, url, hdurl, media_type, copyright
- `CelestialBody` — stores astronomy objects: name, body_type, right_ascension, declination, description
- `Collection` — join table linking an `Apod` to a `CelestialBody`, with a `collected_at` timestamp
- Ran `makemigrations` and `migrate` to create the database tables

### 3. Built the REST API (`apod/serializers.py`, `apod/views.py`, `apod/urls.py`)
- Created `ModelSerializer` for each model (converts Python objects ↔ JSON)
- Created `ListAPIView` for each model (returns all rows as a JSON array)
- Wired up URL routes: `/api/apods/`, `/api/celestial-bodies/`, `/api/collections/`
- Added `ApodDetailView` using `lookup_field = 'date'` for `/api/apods/<date>/`

### 4. Built the Claude astronomy agent (`apod/agents/astronomy_agent.py`)
- Defined tools: `search_previous_apods`, `save_celestial_body`
- Wrote an agentic loop with `max_turns=8` and prompt caching
- Agent reads an APOD, identifies the celestial body, checks for duplicates, saves to DB
- Updated system prompt to provide real RA/Dec from Claude's astronomy knowledge
- Removed hardcoded `lookup_coordinates` dictionary — Claude provides coordinates directly

### 5. Built the management command (`apod/management/commands/fetch_apod.py`)
- Calls NASA APOD API and saves the result to the `Apod` table
- Runs the astronomy agent only when the APOD is newly created (not a duplicate)
- Added optional `date` argument so you can fetch any past APOD: `python manage.py fetch_apod 2026-04-19`

---

## Phase 2 — React Frontend

### 6. Scaffolded the frontend (`frontend/`)
- Created Vite + React + TypeScript project inside `frontend/`
- Configured Vite proxy to forward `/api` requests to Django on port 8000
- Run dev server with `npm run dev` from the `frontend/` directory

### 7. Built the collection grid (`frontend/src/App.tsx`)
- Fetched all three API endpoints on mount using `useEffect`
- Stored results in state with `useState`
- Built a `Set` of collected body IDs for O(1) lookup
- Wrote `getApodForBody` to walk the join table: body → collection → apod
- Rendered a card grid: APOD image, body name, body type, opacity based on collected status
- Fixed type mismatch bug: API returns `apod` and `celestial_body`, not `apod_id` / `celestial_body_id`

---

### 8. Built the sky map (`frontend/src/SkyMap.tsx`)
- SVG-based star map with a dark space background
- Random background star field (200 stars, deterministic positions)
- RA/Dec grid lines for reference
- Collected bodies plotted as glowing blue dots with labels
- Coordinate parser functions: `parseRA` converts `"17h 45m 40s"` → `17.75`, `parseDec` converts `"-29° 00' 00\""` → `-29`
- Bodies with `"unknown"` coordinates are filtered out via null check

### 9. Seeded the database (`apod/management/commands/seed_bodies.py`)
- Created `seed_bodies` management command with 12 well-known objects
- Covers planets, stars, nebulae, galaxies, and clusters
- Uses `get_or_create` to prevent duplicates
- Run with `python manage.py seed_bodies`

### 10. Dark space theme (`frontend/src/index.css`)
- Full dark theme: deep navy background, cold blue accent (#4fc3f7)
- CSS variables for consistent color palette across the app
- Typography: uppercase letter-spaced headings for observatory aesthetic
- Cards: conditional border/opacity communicate collection status

### 11. Built StarFinder (`frontend/src/StarFinder.tsx`)
- Address input → Nominatim geocoding API (free, no key needed) → lat/lon
- `astronomy-engine` converts RA/Dec + lat/lon + current time → altitude/azimuth
- Altitude > 0° means the body is above the horizon and visible tonight
- Bodies sorted by altitude — highest in sky shown first
- Azimuth converted to compass direction (N, NE, E, SE, S, SW, W, NW)
- Clicking a body fires `onBodySelect` → will trigger Astrid narration

---

## Up Next

- [ ] Wire StarFinder into App.tsx
- [ ] Build Astrid sidebar — click a body, she narrates where to look
- [ ] Connect Vellum for natural language narration
- [ ] Add more APODs with `fetch_apod` for past dates
