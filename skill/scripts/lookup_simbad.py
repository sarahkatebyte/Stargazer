"""
Look up a celestial body in the SIMBAD astronomical database.
Returns the canonical name, coordinates, object type, and cross-references.
"""

import sys
import json
import urllib.request
import urllib.parse

SIMBAD_TAP_URL = "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"


def lookup(name):
    """Query SIMBAD by identifier name."""
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
    query = (
        f"SELECT main_id, ra, dec, otype_txt "
        f"FROM basic JOIN ident ON basic.oid = ident.oidref "
        f"WHERE ident.id = 'NAME {name}'"
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


def deg_to_hms(deg):
    """Convert degrees to hours/minutes/seconds string."""
    hours = deg / 15.0
    h = int(hours)
    m = int((hours - h) * 60)
    s = ((hours - h) * 60 - m) * 60
    return f"{h:02d}h {m:02d}m {s:04.1f}s"


def deg_to_dms(deg):
    """Convert degrees to degrees/arcminutes/arcseconds string."""
    sign = "+" if deg >= 0 else "-"
    deg = abs(deg)
    d = int(deg)
    m = int((deg - d) * 60)
    s = ((deg - d) * 60 - m) * 60
    return f"{sign}{d:02d}\u00b0 {m:02d}' {s:04.1f}\""


args = json.loads(sys.argv[1])
name = args["name"]

# Check local database first
try:
    response = urllib.request.urlopen("http://localhost:8000/api/celestial-bodies/")
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
