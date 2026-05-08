"""
Look up a celestial body in the SIMBAD astronomical database.
Returns the canonical name, coordinates, object type, and cross-references.
"""

import os
import sys
import json
import urllib.request
import urllib.parse

# Add scripts dir to path so we can share utilities across tool scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _astronomy_utils import deg_to_hms, deg_to_dms, sanitize_adql_name  # noqa: E402

SIMBAD_TAP_URL = "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"


def lookup(name):
    """Query SIMBAD by identifier name."""
    safe_name = sanitize_adql_name(name)
    query = (
        f"SELECT main_id, ra, dec, otype_txt "
        f"FROM basic JOIN ident ON basic.oid = ident.oidref "
        f"WHERE ident.id = '{safe_name}'"
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
            # Try with NAME prefix (common for well-known objects)
            return lookup_with_prefix(name)

        row = data["data"][0]
        ra_deg = row[1]
        dec_deg = row[2]

        return {
            "found": True,
            "name": name,
            "canonical_id": row[0],
            "object_type": row[3],
            "ra_degrees": round(ra_deg, 4),
            "dec_degrees": round(dec_deg, 4),
            "ra_hms": deg_to_hms(ra_deg),
            "dec_dms": deg_to_dms(dec_deg),
            "simbad_url": f"https://simbad.cds.unistra.fr/simbad/sim-id?Ident={urllib.parse.quote(name)}",
        }
    except Exception as e:
        return {"found": False, "name": name, "error": str(e)}


def lookup_with_prefix(name):
    """Retry with 'NAME' prefix for common names like 'Crab Nebula'."""
    safe_name = sanitize_adql_name(name)
    query = (
        f"SELECT main_id, ra, dec, otype_txt "
        f"FROM basic JOIN ident ON basic.oid = ident.oidref "
        f"WHERE ident.id = 'NAME {safe_name}'"
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
            return {"found": False, "name": name, "error": "Not found in SIMBAD"}

        row = data["data"][0]
        ra_deg = row[1]
        dec_deg = row[2]

        return {
            "found": True,
            "name": name,
            "canonical_id": row[0],
            "object_type": row[3],
            "ra_degrees": round(ra_deg, 4),
            "dec_degrees": round(dec_deg, 4),
            "ra_hms": deg_to_hms(ra_deg),
            "dec_dms": deg_to_dms(dec_deg),
            "simbad_url": f"https://simbad.cds.unistra.fr/simbad/sim-id?Ident={urllib.parse.quote(name)}",
        }
    except Exception as e:
        return {"found": False, "name": name, "error": str(e)}


# deg_to_hms and deg_to_dms live in _astronomy_utils.py — imported above


args = json.loads(sys.argv[1])
name = args["name"]

# Check local database first
try:
    base_url = os.environ.get('STARGAZER_BASE_URL', 'http://localhost:8000').rstrip('/')
    response = urllib.request.urlopen(f"{base_url}/api/celestial-bodies/")
    bodies = json.loads(response.read())
    local_match = next((b for b in bodies if b["name"].lower() == name.lower()), None)
except Exception:
    local_match = None

# Look up in SIMBAD
simbad_result = lookup(name)

output = {
    "simbad": simbad_result,
    "in_local_database": local_match is not None,
}

if local_match:
    output["local_data"] = {
        "name": local_match["name"],
        "body_type": local_match["body_type"],
        "right_ascension": local_match["right_ascension"],
        "declination": local_match["declination"],
        "description": local_match["description"],
    }

print(json.dumps(output))
