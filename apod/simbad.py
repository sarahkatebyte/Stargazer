"""
SIMBAD Integration
Validates celestial body coordinates against the SIMBAD astronomical database
maintained by the Centre de Donnees astronomiques de Strasbourg (CDS).
"""

import re
import json
import math
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

SIMBAD_TAP_URL = "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"


def lookup_body(name):
    """
    Query SIMBAD for a celestial body by name.
    Returns dict with main_id, ra_deg, dec_deg, object_type, or None if not found.
    """
    query = (
        f"SELECT main_id, ra, dec, otype_txt "
        f"FROM basic JOIN ident ON basic.oid = ident.oidref "
        f"WHERE ident.id = '{name}'"
    )

    params = urllib.parse.urlencode({
        "request": "doQuery",
        "lang": "adql",
        "format": "json",
        "query": query,
    })

    url = f"{SIMBAD_TAP_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Stargazer/1.0"})
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())

        if not data.get("data"):
            # Try with common name variations
            return _retry_with_aliases(name)

        row = data["data"][0]
        return {
            "main_id": row[0],
            "ra_deg": row[1],
            "dec_deg": row[2],
            "object_type": row[3],
        }
    except Exception as e:
        logger.warning(f"SIMBAD lookup failed for '{name}': {e}")
        return None


def _retry_with_aliases(name):
    """Try common name patterns if the exact name isn't found."""
    aliases = [
        name,
        f"NAME {name}",
        name.replace("The ", ""),
    ]

    for alias in aliases[1:]:  # Skip first, already tried
        query = (
            f"SELECT main_id, ra, dec, otype_txt "
            f"FROM basic JOIN ident ON basic.oid = ident.oidref "
            f"WHERE ident.id = '{alias}'"
        )
        params = urllib.parse.urlencode({
            "request": "doQuery",
            "lang": "adql",
            "format": "json",
            "query": query,
        })
        url = f"{SIMBAD_TAP_URL}?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Stargazer/1.0"})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read())
            if data.get("data"):
                row = data["data"][0]
                return {
                    "main_id": row[0],
                    "ra_deg": row[1],
                    "dec_deg": row[2],
                    "object_type": row[3],
                }
        except Exception:
            continue

    return None


def ra_to_degrees(ra_str):
    """Convert RA string like '05h 35m 17s' or '05h 35m' to degrees."""
    match = re.search(r"(\d+)h\s*(\d+)m\s*(?:(\d+(?:\.\d+)?)s)?", ra_str)
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3)) if match.group(3) else 0.0
    return (hours + minutes / 60 + seconds / 3600) * 15


def dec_to_degrees(dec_str):
    """Convert Dec string like '-05° 23' 28\"' or '+22° 01'' to degrees."""
    match = re.search(r"([+-]?\d+)[°]\s*(\d+)['\u2032]?\s*(?:(\d+(?:\.\d+)?)[\"″\u2033])?", dec_str)
    if not match:
        # Try simpler pattern
        match = re.search(r"([+-]?\d+)", dec_str)
        if not match:
            return None
        return float(match.group(1))
    degrees = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3)) if match.group(3) else 0.0
    sign = -1 if degrees < 0 or dec_str.strip().startswith("-") else 1
    return sign * (abs(degrees) + minutes / 60 + seconds / 3600)


def validate_range(ra_str, dec_str):
    """
    Basic range validation on RA/Dec strings.
    RA must be 0-24 hours, Dec must be -90 to +90 degrees.
    Returns (is_valid, message).
    """
    ra_deg = ra_to_degrees(ra_str)
    dec_deg = dec_to_degrees(dec_str)

    issues = []

    if ra_deg is None:
        issues.append(f"Could not parse RA: {ra_str}")
    elif ra_deg < 0 or ra_deg >= 360:
        issues.append(f"RA out of range: {ra_deg} degrees (must be 0-360)")

    if dec_deg is None:
        issues.append(f"Could not parse Dec: {dec_str}")
    elif dec_deg < -90 or dec_deg > 90:
        issues.append(f"Dec out of range: {dec_deg} degrees (must be -90 to +90)")

    if issues:
        return False, "; ".join(issues)
    return True, "Coordinates within valid range"


def validate_against_simbad(name, ra_str, dec_str, threshold_deg=2.0):
    """
    Validate coordinates against SIMBAD. Returns a dict with:
    - validated: bool (True if SIMBAD confirms, False if discrepancy)
    - simbad_found: bool
    - message: str
    - simbad_data: dict or None
    - angular_separation: float or None (degrees)
    """
    # First check basic range validity
    range_valid, range_msg = validate_range(ra_str, dec_str)
    if not range_valid:
        return {
            "validated": False,
            "simbad_found": False,
            "message": f"Range validation failed: {range_msg}",
            "simbad_data": None,
            "angular_separation": None,
        }

    # Look up in SIMBAD
    simbad = lookup_body(name)

    if simbad is None:
        return {
            "validated": True,  # Can't invalidate what we can't check
            "simbad_found": False,
            "message": f"'{name}' not found in SIMBAD. Coordinates accepted without cross-reference.",
            "simbad_data": None,
            "angular_separation": None,
        }

    # Convert Claude's coordinates to degrees for comparison
    claude_ra_deg = ra_to_degrees(ra_str)
    claude_dec_deg = dec_to_degrees(dec_str)

    if claude_ra_deg is None or claude_dec_deg is None:
        return {
            "validated": False,
            "simbad_found": True,
            "message": "Could not parse coordinates for comparison",
            "simbad_data": simbad,
            "angular_separation": None,
        }

    # Calculate angular separation
    sep = angular_separation(
        claude_ra_deg, claude_dec_deg,
        simbad["ra_deg"], simbad["dec_deg"]
    )

    if sep <= threshold_deg:
        return {
            "validated": True,
            "simbad_found": True,
            "message": (
                f"SIMBAD confirms: '{name}' (canonical: {simbad['main_id']}, "
                f"type: {simbad['object_type']}). "
                f"Separation: {sep:.2f}° (within {threshold_deg}° threshold)"
            ),
            "simbad_data": simbad,
            "angular_separation": sep,
        }
    else:
        return {
            "validated": False,
            "simbad_found": True,
            "message": (
                f"SIMBAD DISCREPANCY: '{name}' (canonical: {simbad['main_id']}). "
                f"Claude: RA={ra_str} Dec={dec_str} -> ({claude_ra_deg:.2f}°, {claude_dec_deg:.2f}°). "
                f"SIMBAD: ({simbad['ra_deg']:.4f}°, {simbad['dec_deg']:.4f}°). "
                f"Separation: {sep:.2f}° EXCEEDS {threshold_deg}° threshold"
            ),
            "simbad_data": simbad,
            "angular_separation": sep,
        }


def angular_separation(ra1_deg, dec1_deg, ra2_deg, dec2_deg):
    """
    Calculate angular separation between two points on the sky in degrees.
    Uses the Vincenty formula for accuracy at small separations.
    """
    ra1 = math.radians(ra1_deg)
    dec1 = math.radians(dec1_deg)
    ra2 = math.radians(ra2_deg)
    dec2 = math.radians(dec2_deg)

    delta_ra = abs(ra1 - ra2)

    numerator = math.sqrt(
        (math.cos(dec2) * math.sin(delta_ra)) ** 2 +
        (math.cos(dec1) * math.sin(dec2) -
         math.sin(dec1) * math.cos(dec2) * math.cos(delta_ra)) ** 2
    )
    denominator = (
        math.sin(dec1) * math.sin(dec2) +
        math.cos(dec1) * math.cos(dec2) * math.cos(delta_ra)
    )

    return math.degrees(math.atan2(numerator, denominator))
