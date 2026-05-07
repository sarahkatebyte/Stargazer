"""
Astrid tool functions for Vellum's ToolCallingNode.

Each function is a thin HTTP client that calls the tool execution endpoints
on the Stargazer Django app. This lets Vellum's hosted workflow runner call
tools that actually execute on the Railway server (where the scripts live).

STARGAZER_BASE_URL env var controls where requests go:
  - Production: https://stargazer-production-d04d.up.railway.app
  - Local dev:  http://localhost:8000

Vellum auto-generates the JSON schema for each tool from the function signature
and docstring - so the signature IS the contract. Keep them precise.
"""

import json
import os

import requests

_BASE_URL = os.environ.get(
    'STARGAZER_BASE_URL',
    'https://stargazer-production-d04d.up.railway.app'
).rstrip('/')


def _call_tool(tool_name: str, tool_input: dict) -> str:
    """POST to the tool endpoint on the Django app and return the output string."""
    url = f'{_BASE_URL}/api/tools/{tool_name}/'
    try:
        response = requests.post(url, json=tool_input, timeout=20)
        response.raise_for_status()
        return response.json().get('output', json.dumps({'error': 'No output returned'}))
    except requests.Timeout:
        return json.dumps({'error': f'Tool {tool_name} timed out'})
    except requests.RequestException as e:
        return json.dumps({'error': f'Tool request failed: {str(e)}'})


def get_celestial_bodies() -> str:
    """Get all celestial bodies in the Stargazer collection, including their coordinates and type."""
    return _call_tool('get_celestial_bodies', {})


def get_todays_apod() -> str:
    """Get today's NASA Astronomy Picture of the Day, including the title, explanation, and image URL."""
    return _call_tool('get_todays_apod', {})


def get_visible_tonight(
    address: str = None,
    latitude: float = None,
    longitude: float = None,
) -> str:
    """Calculate which celestial bodies are visible tonight from a given location.

    Accepts a street address (preferred) or latitude/longitude coordinates.

    Args:
        address: Street address, city, or place name (e.g. '173 Hart Street Brooklyn NY')
        latitude: Observer's latitude in decimal degrees (fallback if no address)
        longitude: Observer's longitude in decimal degrees (fallback if no address)
    """
    tool_input = {}
    if address:
        tool_input['address'] = address
    if latitude is not None:
        tool_input['latitude'] = latitude
    if longitude is not None:
        tool_input['longitude'] = longitude
    return _call_tool('get_visible_tonight', tool_input)


def lookup_simbad(name: str) -> str:
    """Look up a celestial body in the SIMBAD astronomical reference database.

    Returns the canonical scientific name, authoritative coordinates, object type,
    and checks if the body is in the local Stargazer database.
    Use this for deep-sky objects: stars, nebulae, galaxies, star clusters.

    Args:
        name: Name of the celestial body (e.g. 'Crab Nebula', 'Betelgeuse', 'M31')
    """
    return _call_tool('lookup_simbad', {'name': name})


def lookup_jpl_horizons(name: str, date: str = None) -> str:
    """Look up a solar system body in NASA/JPL Horizons. Returns current RA/Dec coordinates.

    Use this for objects INSIDE the solar system: planets, moons, comets, asteroids.
    For deep-sky objects (stars, nebulae, galaxies) use lookup_simbad instead.

    Args:
        name: Name of the solar system body (e.g. 'Mars', 'Saturn', 'Moon', 'C/2025 R3')
        date: Observation date in YYYY-MM-DD format (defaults to today)
    """
    input_data = {'name': name}
    if date:
        input_data['date'] = date
    return _call_tool('lookup_jpl_horizons', input_data)
