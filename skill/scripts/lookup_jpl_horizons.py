"""
Look up a solar system body in NASA/JPL's Horizons system.
Returns the body name, current RA/Dec, and body type.
Covers planets, moons, comets, and asteroids - objects inside the solar system.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.parse

# Add scripts dir to path so we can share utilities across tool scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _astronomy_utils import deg_to_hms, deg_to_dms  # noqa: E402
from datetime import date, datetime, timedelta

HORIZONS_API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Map common names to JPL Horizons body IDs
SOLAR_SYSTEM_BODIES = {
    "mercury": "199",
    "venus": "299",
    "mars": "499",
    "jupiter": "599",
    "saturn": "699",
    "uranus": "799",
    "neptune": "899",
    "pluto": "999",
    "moon": "301",
    "the moon": "301",
    "sun": "10",
    "io": "501",
    "europa": "502",
    "ganymede": "503",
    "callisto": "504",
    "titan": "606",
    "enceladus": "602",
    "triton": "801",
}

BODY_TYPES = {
    "199": "Planet", "299": "Planet", "499": "Planet",
    "599": "Planet", "699": "Planet", "799": "Planet",
    "899": "Planet", "999": "Dwarf Planet", "301": "Natural Satellite",
    "10": "Star", "501": "Natural Satellite", "502": "Natural Satellite",
    "503": "Natural Satellite", "504": "Natural Satellite",
    "606": "Natural Satellite", "602": "Natural Satellite",
    "801": "Natural Satellite",
}


# deg_to_hms and deg_to_dms live in _astronomy_utils.py — imported above


def lookup(name, obs_date=None):
    normalized = name.lower().strip()

    if obs_date is None:
        obs_date = date.today().isoformat()

    # Get the JPL command
    if normalized in SOLAR_SYSTEM_BODIES:
        command = SOLAR_SYSTEM_BODIES[normalized]
    elif re.match(r"^[CPDI]/", name):
        command = f"DES={name};"
    elif re.match(r"^\d+P/", name):
        command = f"DES={name};"
    else:
        command = f"{name};"

    # Build next-day for stop time
    start_dt = datetime.strptime(obs_date, "%Y-%m-%d")
    stop_date = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'500@399'",
        "START_TIME": f"'{obs_date}'",
        "STOP_TIME": f"'{stop_date}'",
        "STEP_SIZE": "'1 d'",
        "QUANTITIES": "'1'",
        "ANG_FORMAT": "'DEG'",
        "CSV_FORMAT": "'YES'",
    }

    _safe = "'"
    url = f"{HORIZONS_API_URL}?{urllib.parse.urlencode(params, safe=_safe)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Stargazer/1.0"})
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read())
        result_text = data.get("result", "")

        if "Multiple" in result_text or "No matches" in result_text or "Cannot find" in result_text:
            return {"found": False, "name": name, "error": "Not found in JPL Horizons"}

        # Parse between $$SOE and $$EOE
        soe_match = re.search(r"\$\$SOE\n(.+?)\n\$\$EOE", result_text, re.DOTALL)
        if not soe_match:
            return {"found": False, "name": name, "error": "Could not parse ephemeris"}

        first_line = soe_match.group(1).strip().split("\n")[0]
        fields = [f.strip() for f in first_line.split(",")]

        ra_deg = float(fields[3])
        dec_deg = float(fields[4])

        # Extract target body name
        body_name_match = re.search(r"Target body name:\s*(.+?)\s*\{", result_text)
        body_name = body_name_match.group(1).strip() if body_name_match else name

        body_type = BODY_TYPES.get(command, "Solar System Object")

        return {
            "found": True,
            "name": name,
            "jpl_name": body_name,
            "body_type": body_type,
            "ra_degrees": round(ra_deg, 5),
            "dec_degrees": round(dec_deg, 5),
            "ra_hms": deg_to_hms(ra_deg),
            "dec_dms": deg_to_dms(dec_deg),
            "observation_date": obs_date,
            "source": "NASA/JPL Horizons System",
        }

    except Exception as e:
        return {"found": False, "name": name, "error": str(e)}


args = json.loads(sys.argv[1])
name = args["name"]
obs_date = args.get("date", None)

result = lookup(name, obs_date)

# Also check local database
try:
    base_url = os.environ.get('STARGAZER_BASE_URL', 'http://localhost:8000').rstrip('/')
    response = urllib.request.urlopen(f"{base_url}/api/celestial-bodies/")
    bodies = json.loads(response.read())
    local_match = next((b for b in bodies if b["name"].lower() == name.lower()), None)
except Exception:
    local_match = None

output = {
    "jpl_horizons": result,
    "in_local_database": local_match is not None,
}

if local_match:
    output["local_data"] = {
        "name": local_match["name"],
        "body_type": local_match["body_type"],
        "right_ascension": local_match["right_ascension"],
        "declination": local_match["declination"],
    }

print(json.dumps(output))
