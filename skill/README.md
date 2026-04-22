# Stargazer Skill for Vellum

This skill connects your Vellum assistant to the Stargazer astronomy app. Once loaded, your assistant can tell you what's in the sky tonight, show you NASA's Astronomy Picture of the Day, and explain celestial bodies in plain language - all from a conversational interface.

## Prerequisites

- [Vellum](https://vellum.ai) installed on macOS
- The Stargazer Django backend running locally on port 8000 (see the main [README](../README.md) for setup)

## Setup

### 1. Start the Django backend

```bash
cd stargazer
source venv/bin/activate
python manage.py runserver
```

Make sure `http://localhost:8000/api/celestial-bodies/` returns data before proceeding.

### 2. Copy the skill into your Vellum workspace

Find your Vellum workspace skills directory. It's usually at:

```
~/.local/share/vellum/assistants/<your-assistant-id>/.vellum/workspace/skills/
```

Copy the `skill/` folder from this repo into that directory and rename it to `stargazer`:

```bash
cp -r skill/ ~/.local/share/vellum/assistants/<your-assistant-id>/.vellum/workspace/skills/stargazer
```

> **Tip:** If you're not sure where your workspace is, ask your assistant: *"Where is your workspace directory?"*

### 3. Load the skill

In a conversation with your assistant, say:

> "Load the Stargazer skill"

Your assistant will confirm it's loaded and you'll have three new tools available.

## Usage

Once the skill is loaded and Django is running, try:

- **"What's in the sky tonight from [your address]?"**
- **"Show me today's Astronomy Picture of the Day"**
- **"Tell me about the celestial bodies in the collection"**
- **"What's visible tonight from 26 W 23rd St, New York?"**

The assistant will respond in warm, plain language with compass directions and the fist trick for altitude (one fist at arm's length ≈ 10° of sky).

## Tools

| Tool | What it does |
|---|---|
| `get_visible_tonight` | Takes an address (or lat/lon), geocodes it, calculates which bodies are above the horizon right now |
| `get_todays_apod` | Fetches today's APOD from the Django API |
| `get_celestial_bodies` | Returns the full catalog of tracked celestial bodies |

## How it works

```
You ask a question
    ↓
Your assistant decides which tool to call
    ↓
Vellum runs the matching Python script in scripts/
    ↓
The script calls the Django API at localhost:8000
    ↓
The script does geocoding (Nominatim) and astronomy math
    ↓
Results come back as JSON
    ↓
Your assistant narrates the results using the style from SKILL.md
```

The assistant never talks to the database directly - everything goes through the REST API. The scripts are the bridge between your assistant and your data.
