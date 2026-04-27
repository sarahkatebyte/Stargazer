"""
JPL Horizons Integration
Validates solar system body coordinates against NASA/JPL's Horizons system.
Complements SIMBAD (which covers deep-sky objects) by covering planets,
moons, comets, and asteroids - objects INSIDE the solar system.

Horizons is maintained by the Solar System Dynamics Group at JPL, Pasadena, CA.
API docs: https://ssd-api.jpl.nasa.gov/doc/horizons.html
"""

import re
import json
import math
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

HORIZONS_API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Map common names to JPL Horizons body IDs
# Planets use the x99 convention, moons use specific IDs
SOLAR_SYSTEM_BODIES = {
    "mercury": "199",
    "venus": "299",
    "earth": "399",
    "mars": "499",
    "jupiter": "599",
    "saturn": "699",
    "uranus": "799",
    "neptune": "899",
    "pluto": "999",
    "moon": "301",
    "the moon": "301",
    "sun": "10",
    "the sun": "10",
    # Major moons
    "io": "501",
    "europa": "502",
    "ganymede": "503",
    "callisto": "504",
    "titan": "606",
    "enceladus": "602",
    "triton": "801",
    "charon": "901",
    # Dwarf planets
    "ceres": "1;",
    "eris": "136199;",
    "haumea": "136108;",
    "makemake": "136472;",
}

# Body types for solar system objects
BODY_TYPES = {
    "199": "Planet",
    "299": "Planet",
    "399": "Planet",
    "499": "Planet",
    "599": "Planet",
    "699": "Planet",
    "799": "Planet",
    "899": "Planet",
    "999": "Dwarf Planet",
    "301": "Natural Satellite",
    "10": "Star",
    "501": "Natural Satellite",
    "502": "Natural Satellite",
    "503": "Natural Satellite",
    "504": "Natural Satellite",
    "606": "Natural Satellite",
    "602": "Natural Satellite",
    "801": "Natural Satellite",
    "901": "Natural Satellite",
    "1;": "Dwarf Planet",
    "136199;": "Dwarf Planet",
    "136108;": "Dwarf Planet",
    "136472;": "Dwarf Planet",
}


def is_solar_system_body(name):
    """Check if a name looks like a solar system object."""
    normalized = name.lower().strip()

    # Direct match in our known bodies
    if normalized in SOLAR_SYSTEM_BODIES:
        return True

    # Comet designations (e.g., C/2025 R3, 1P/Halley)
    if re.match(r"^[CPDI]/", name) or re.match(r"^\d+P/", name):
        return True

    return False


def _get_body_command(name):
    """Convert a body name to a JPL Horizons COMMAND parameter."""
    normalized = name.lower().strip()

    # Direct lookup
    if normalized in SOLAR_SYSTEM_BODIES:
        return SOLAR_SYSTEM_BODIES[normalized]

    # Comet designation - use DES= syntax with semicolon
    comet_match = re.match(r"^([CPDI]/[\w\s\-()]+)", name)
    if comet_match:
        return f"DES={comet_match.group(1)};"

    # Numbered comet (e.g., "1P/Halley")
    numbered_comet = re.match(r"^(\d+P/\w+)", name)
    if numbered_comet:
        return f"DES={numbered_comet.group(1)};"

    # Fall back to name search
    return f"{name};"


def lookup_body(name, date=None):
    """
    Query JPL Horizons for a solar system body's RA/Dec on a given date.
    Returns dict with body_name, ra_deg, dec_deg, body_type, or None if not found.

    Args:
        name: Body name (e.g., "Mars", "Saturn", "C/2025 R3")
        date: Observation date as string "YYYY-MM-DD" (defaults to today)
    """
    if date is None:
        from datetime import date as dt_date
        date = dt_date.today().isoformat()

    command = _get_body_command(name)

    # Build next-day for stop time
    from datetime import datetime, timedelta
    start_dt = datetime.strptime(date, "%Y-%m-%d")
    stop_date = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'500@399'",
        "START_TIME": f"'{date}'",
        "STOP_TIME": f"'{stop_date}'",
        "STEP_SIZE": "'1 d'",
        "QUANTITIES": "'1'",
        "ANG_FORMAT": "'DEG'",
        "CSV_FORMAT": "'YES'",
    }

    safe_chars = "'"
    url = f"{HORIZONS_API_URL}?{urllib.parse.urlencode(params, safe=safe_chars)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Stargazer/1.0"})
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read())

        result_text = data.get("result", "")

        # Check for multiple matches or errors
        if "Multiple" in result_text and "Use ID#" in result_text:
            logger.info(f"JPL Horizons: multiple matches for '{name}', trying with ID")
            return None

        if "No matches found" in result_text or "Cannot find" in result_text:
            logger.info(f"JPL Horizons: '{name}' not found")
            return None

        # Parse RA/Dec from between $$SOE and $$EOE markers
        soe_match = re.search(r"\$\$SOE\n(.+?)\n\$\$EOE", result_text, re.DOTALL)
        if not soe_match:
            logger.warning(f"JPL Horizons: could not parse ephemeris for '{name}'")
            return None

        # First data line (CSV format): date, , , RA, DEC,
        first_line = soe_match.group(1).strip().split("\n")[0]
        fields = [f.strip() for f in first_line.split(",")]

        # RA and DEC are in fields[3] and fields[4]
        ra_deg = float(fields[3])
        dec_deg = float(fields[4])

        # Extract target body name from result
        body_name_match = re.search(r"Target body name:\s*(.+?)\s*\{", result_text)
        body_name = body_name_match.group(1).strip() if body_name_match else name

        # Determine body type
        body_type = BODY_TYPES.get(command, "Solar System Object")

        return {
            "body_name": body_name,
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "body_type": body_type,
            "date": date,
        }

    except Exception as e:
        logger.warning(f"JPL Horizons lookup failed for '{name}': {e}")
        return None


def validate_against_horizons(name, ra_str, dec_str, date=None, threshold_deg=5.0):
    """
    Validate coordinates against JPL Horizons. Returns a dict with:
    - validated: bool
    - horizons_found: bool
    - message: str
    - horizons_data: dict or None
    - angular_separation: float or None (degrees)

    Uses a larger threshold (5 deg) than SIMBAD (2 deg) because planets
    move significantly, and Claude's coordinates may be for a different
    date than the APOD observation.
    """
    from apod.simbad import ra_to_degrees, dec_to_degrees, angular_separation

    # Look up in JPL Horizons
    horizons = lookup_body(name, date)

    if horizons is None:
        return {
            "validated": True,  # Can't invalidate what we can't check
            "horizons_found": False,
            "message": f"'{name}' not found in JPL Horizons.",
            "horizons_data": None,
            "angular_separation": None,
        }

    # Convert Claude's coordinates to degrees
    claude_ra_deg = ra_to_degrees(ra_str)
    claude_dec_deg = dec_to_degrees(dec_str)

    if claude_ra_deg is None or claude_dec_deg is None:
        return {
            "validated": False,
            "horizons_found": True,
            "message": "Could not parse coordinates for comparison",
            "horizons_data": horizons,
            "angular_separation": None,
        }

    # Calculate angular separation
    sep = angular_separation(
        claude_ra_deg, claude_dec_deg,
        horizons["ra_deg"], horizons["dec_deg"]
    )

    if sep <= threshold_deg:
        return {
            "validated": True,
            "horizons_found": True,
            "message": (
                f"JPL Horizons confirms: '{name}' ({horizons['body_name']}, "
                f"type: {horizons['body_type']}). "
                f"Separation: {sep:.2f}° (within {threshold_deg}° threshold)"
            ),
            "horizons_data": horizons,
            "angular_separation": sep,
        }
    else:
        return {
            "validated": False,
            "horizons_found": True,
            "message": (
                f"JPL Horizons DISCREPANCY: '{name}' ({horizons['body_name']}). "
                f"Claude: RA={ra_str} Dec={dec_str} -> ({claude_ra_deg:.2f}°, {claude_dec_deg:.2f}°). "
                f"Horizons ({horizons['date']}): ({horizons['ra_deg']:.4f}°, {horizons['dec_deg']:.4f}°). "
                f"Separation: {sep:.2f}° EXCEEDS {threshold_deg}° threshold"
            ),
            "horizons_data": horizons,
            "angular_separation": sep,
        }
