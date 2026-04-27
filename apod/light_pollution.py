"""
Light Pollution & Visibility Assessment

Determines sky darkness (Bortle class) for a location and assesses
whether specific celestial bodies are visible given light conditions.

Data source: Curated lookup table with nearest-match interpolation.
Upgrade path: GeoTIFF processing from the World Atlas of Artificial
Night Sky Brightness (Falchi et al., 2016).
"""

import math

# Bortle class descriptions - what the sky actually looks like
BORTLE_DESCRIPTIONS = {
    1: "Excellent dark site",
    2: "Typical dark site",
    3: "Rural sky",
    4: "Rural/suburban transition",
    5: "Suburban sky",
    6: "Bright suburban",
    7: "Suburban/urban transition",
    8: "City sky",
    9: "Inner-city sky",
}

# Reference locations with known Bortle values
# Each entry: (lat, lon, bortle_class, name)
# Sources: lightpollutionmap.info, field measurements, community data
REFERENCE_LOCATIONS = [
    # NYC metro
    (40.7580, -73.9855, 9, "Midtown Manhattan"),
    (40.6938, -73.9445, 8, "Bushwick/Bed-Stuy Brooklyn"),
    (40.6501, -73.9496, 8, "Flatbush Brooklyn"),
    (40.5731, -73.9712, 7, "Coney Island"),
    (40.8448, -73.8648, 8, "Bronx"),
    (40.7282, -73.7949, 8, "Queens"),
    (40.5795, -74.1502, 7, "Staten Island"),

    # Upstate NY / Hudson Valley
    (42.2529, -73.7910, 5, "Hudson NY"),
    (42.0987, -74.0060, 4, "Catskills"),
    (44.1120, -73.9237, 3, "Adirondacks"),
    (41.4045, -74.3132, 5, "Catskill Mountains southern"),
    (42.4440, -76.5019, 4, "Finger Lakes"),
    (43.1610, -73.7562, 4, "Saratoga region"),

    # NJ / CT / PA nearby
    (40.7440, -74.0324, 9, "Jersey City"),
    (40.9176, -74.1719, 7, "Northern NJ suburbs"),
    (41.0534, -73.5387, 7, "Stamford CT"),
    (41.7658, -72.6734, 6, "Hartford CT"),
    (40.6084, -75.4902, 5, "Lehigh Valley PA"),

    # Other US cities (for travel/comparison)
    (34.0522, -118.2437, 9, "Los Angeles"),
    (41.8781, -87.6298, 9, "Chicago"),
    (42.3601, -71.0589, 8, "Boston"),
    (37.7749, -122.4194, 8, "San Francisco"),
    (38.9072, -77.0369, 8, "Washington DC"),
    (29.7604, -95.3698, 8, "Houston"),
    (33.4484, -112.0740, 7, "Phoenix"),
    (39.7392, -104.9903, 7, "Denver"),
    (47.6062, -122.3321, 7, "Seattle"),
    (35.2271, -80.8431, 7, "Charlotte"),
    (30.2672, -97.7431, 7, "Austin"),

    # Dark sky sites
    (36.8629, -111.3743, 2, "Grand Canyon North Rim"),
    (38.5733, -109.5498, 2, "Canyonlands UT"),
    (32.7795, -105.8200, 1, "White Sands NM"),
    (31.9474, -111.5967, 1, "Kitt Peak AZ"),
    (36.4622, -116.8666, 1, "Death Valley"),
]

# Visibility thresholds: max Bortle class where each body type is visible
# Higher number = visible in worse conditions
VISIBILITY_THRESHOLDS = {
    # Planets are bright - visible even in the worst city sky
    "Planet": {"naked_eye": 9, "binoculars": 9, "telescope": 9},

    # Bright stars punch through city light
    "Star": {"naked_eye": 8, "binoculars": 9, "telescope": 9},

    # Star clusters need somewhat dark skies for naked eye
    "Star Cluster": {"naked_eye": 5, "binoculars": 7, "telescope": 9},

    # Nebulae vary a lot, using Orion Nebula as baseline (brightest)
    "Nebula": {"naked_eye": 5, "binoculars": 7, "telescope": 8},

    # Galaxies need dark skies for naked eye (Andromeda is the benchmark)
    "Galaxy": {"naked_eye": 4, "binoculars": 6, "telescope": 8},

    # The Milky Way structure needs genuinely dark skies
    "Milky Way": {"naked_eye": 4, "binoculars": 5, "telescope": 6},

    # Default for anything unclassified
    "default": {"naked_eye": 5, "binoculars": 7, "telescope": 9},
}


def get_bortle_class(lat, lon):
    """
    Determine Bortle class for a location using nearest reference point.

    Returns dict with bortle_class, description, reference_name, and
    distance_km to the matched reference point.
    """
    best_match = None
    best_distance = float("inf")

    for ref_lat, ref_lon, bortle, name in REFERENCE_LOCATIONS:
        distance = _haversine(lat, lon, ref_lat, ref_lon)
        if distance < best_distance:
            best_distance = distance
            best_match = (bortle, name)

    bortle_class, ref_name = best_match

    return {
        "bortle_class": bortle_class,
        "description": BORTLE_DESCRIPTIONS[bortle_class],
        "reference_location": ref_name,
        "distance_km": round(best_distance, 1),
        "confidence": _confidence_from_distance(best_distance),
    }


def assess_visibility(body_type, bortle_class):
    """
    Determine how a celestial body can be observed at a given Bortle class.

    Returns one of: "naked_eye", "binoculars", "telescope", "not_visible"
    """
    thresholds = VISIBILITY_THRESHOLDS.get(
        body_type, VISIBILITY_THRESHOLDS["default"]
    )

    if bortle_class <= thresholds["naked_eye"]:
        return "naked_eye"
    elif bortle_class <= thresholds["binoculars"]:
        return "binoculars"
    elif bortle_class <= thresholds["telescope"]:
        return "telescope"
    else:
        return "not_visible"


def get_visibility_summary(bodies, bortle_class):
    """
    Assess visibility for a list of celestial bodies at a given Bortle class.
    Each body dict should have 'name' and 'body_type' keys.

    Returns list of dicts with visibility assessment added.
    """
    results = []
    for body in bodies:
        visibility = assess_visibility(body["body_type"], bortle_class)
        results.append({
            **body,
            "visibility": visibility,
            "visibility_label": _visibility_label(visibility),
        })
    return results


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _confidence_from_distance(distance_km):
    """
    How confident are we in this Bortle reading?
    Closer to a reference point = higher confidence.
    """
    if distance_km < 10:
        return "high"
    elif distance_km < 50:
        return "medium"
    else:
        return "low"


def _visibility_label(visibility):
    """Human-friendly visibility label."""
    return {
        "naked_eye": "Visible to the naked eye",
        "binoculars": "Binoculars recommended",
        "telescope": "Telescope needed",
        "not_visible": "Not visible from this location",
    }[visibility]
