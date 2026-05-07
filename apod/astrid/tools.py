"""
Astrid tool functions for Vellum's ToolCallingNode.

Each function is a thin wrapper around the existing subprocess-based tool runner.
Vellum auto-generates the JSON schema for each tool from the function signature
and docstring - so the signature IS the contract. Keep them precise.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / 'skill' / 'scripts'


def _run_script(tool_name: str, tool_input: dict) -> str:
    """Execute a tool script as a subprocess and return its output."""
    script_path = SCRIPTS_DIR / f'{tool_name}.py'

    if not script_path.exists():
        return json.dumps({'error': f'Unknown tool: {tool_name}'})

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), json.dumps(tool_input)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(SCRIPTS_DIR),
        )
        if result.returncode != 0:
            return json.dumps({
                'error': f'Tool {tool_name} failed',
                'details': result.stderr[:500] if result.stderr else 'Unknown error'
            })
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return json.dumps({'error': f'Tool {tool_name} timed out after 15 seconds'})
    except Exception as e:
        return json.dumps({'error': f'Tool execution error: {str(e)}'})


def get_celestial_bodies() -> str:
    """Get all celestial bodies in the Stargazer collection, including their coordinates and type."""
    return _run_script('get_celestial_bodies', {})


def get_todays_apod() -> str:
    """Get today's NASA Astronomy Picture of the Day, including the title, explanation, and image URL."""
    return _run_script('get_todays_apod', {})


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
    input_data = {}
    if address:
        input_data['address'] = address
    if latitude is not None:
        input_data['latitude'] = latitude
    if longitude is not None:
        input_data['longitude'] = longitude
    return _run_script('get_visible_tonight', input_data)


def lookup_simbad(name: str) -> str:
    """Look up a celestial body in the SIMBAD astronomical reference database.

    Returns the canonical scientific name, authoritative coordinates, object type,
    and checks if the body is in the local Stargazer database.
    Use this for deep-sky objects: stars, nebulae, galaxies, star clusters.

    Args:
        name: Name of the celestial body (e.g. 'Crab Nebula', 'Betelgeuse', 'M31')
    """
    return _run_script('lookup_simbad', {'name': name})


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
    return _run_script('lookup_jpl_horizons', input_data)
