import os
import sys
import json
import math
import urllib.request
from datetime import datetime, timezone


def geocode_address(address):
    """Convert an address string to lat/lon using Nominatim (OpenStreetMap)."""
    url = 'https://nominatim.openstreetmap.org/search?q={}&format=json&limit=1'.format(
        urllib.request.quote(address)
    )
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Stargazer/1.0',
        'Accept-Language': 'en',
    })
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    if not data:
        raise ValueError(f'Could not geocode address: {address}')
    return {
        'lat': float(data[0]['lat']),
        'lon': float(data[0]['lon']),
        'display_name': data[0]['display_name'],
    }


def parse_ra(ra):
    import re
    match = re.search(r'(\d+)h\s*(\d+)m', ra)
    if not match:
        return None
    return int(match.group(1)) + int(match.group(2)) / 60


def parse_dec(dec):
    import re
    match = re.search(r'([+-]?\d+)\u00b0', dec)
    if not match:
        return None
    return int(match.group(1))


def ra_dec_to_alt_az(ra_hours, dec_deg, lat, lon):
    now = datetime.now(timezone.utc)
    jd = (now.timestamp() / 86400.0) + 2440587.5
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    lst = (gmst + lon) % 360
    ha = lst - ra_hours * 15
    dec_rad = math.radians(dec_deg)
    lat_rad = math.radians(lat)
    ha_rad = math.radians(ha)
    alt = math.asin(
        math.sin(dec_rad) * math.sin(lat_rad) +
        math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad)
    )
    az = math.atan2(
        -math.cos(dec_rad) * math.cos(lat_rad) * math.sin(ha_rad),
        math.sin(dec_rad) - math.sin(lat_rad) * math.sin(alt)
    )
    return math.degrees(alt), (math.degrees(az) + 360) % 360


def az_to_direction(az):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    return dirs[round(az / 45) % 8]


# --- Light pollution / Bortle ---

BORTLE_DESCRIPTIONS = {
    1: "Excellent dark site", 2: "Typical dark site",
    3: "Rural sky", 4: "Rural/suburban transition",
    5: "Suburban sky", 6: "Bright suburban",
    7: "Suburban/urban transition", 8: "City sky",
    9: "Inner-city sky",
}

REFERENCE_LOCATIONS = [
    (40.7580, -73.9855, 9, "Midtown Manhattan"),
    (40.6938, -73.9445, 8, "Bushwick/Bed-Stuy Brooklyn"),
    (40.6501, -73.9496, 8, "Flatbush Brooklyn"),
    (40.5731, -73.9712, 7, "Coney Island"),
    (42.2529, -73.7910, 5, "Hudson NY"),
    (42.0987, -74.0060, 4, "Catskills"),
    (44.1120, -73.9237, 3, "Adirondacks"),
    (41.4045, -74.3132, 5, "Catskill Mountains southern"),
    (40.7440, -74.0324, 9, "Jersey City"),
    (40.9176, -74.1719, 7, "Northern NJ suburbs"),
    (34.0522, -118.2437, 9, "Los Angeles"),
    (41.8781, -87.6298, 9, "Chicago"),
    (42.3601, -71.0589, 8, "Boston"),
    (37.7749, -122.4194, 8, "San Francisco"),
    (38.9072, -77.0369, 8, "Washington DC"),
    (47.6062, -122.3321, 7, "Seattle"),
    (30.2672, -97.7431, 7, "Austin"),
    (39.7392, -104.9903, 7, "Denver"),
    (36.8629, -111.3743, 2, "Grand Canyon North Rim"),
    (32.7795, -105.8200, 1, "White Sands NM"),
    (31.9474, -111.5967, 1, "Kitt Peak AZ"),
]

VISIBILITY_THRESHOLDS = {
    "Planet": {"naked_eye": 9, "binoculars": 9, "telescope": 9},
    "Star": {"naked_eye": 8, "binoculars": 9, "telescope": 9},
    "Star Cluster": {"naked_eye": 5, "binoculars": 7, "telescope": 9},
    "Nebula": {"naked_eye": 5, "binoculars": 7, "telescope": 8},
    "Galaxy": {"naked_eye": 4, "binoculars": 6, "telescope": 8},
    "default": {"naked_eye": 5, "binoculars": 7, "telescope": 9},
}

VISIBILITY_LABELS = {
    "naked_eye": "Visible to the naked eye",
    "binoculars": "Binoculars recommended",
    "telescope": "Telescope needed",
    "not_visible": "Not visible from this location",
}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_bortle_class(lat, lon):
    best_match = None
    best_distance = float('inf')
    for ref_lat, ref_lon, bortle, name in REFERENCE_LOCATIONS:
        distance = haversine(lat, lon, ref_lat, ref_lon)
        if distance < best_distance:
            best_distance = distance
            best_match = (bortle, name)
    bortle_class, ref_name = best_match
    confidence = "high" if best_distance < 10 else "medium" if best_distance < 50 else "low"
    return {
        'bortle_class': bortle_class,
        'description': BORTLE_DESCRIPTIONS[bortle_class],
        'reference_location': ref_name,
        'distance_km': round(best_distance, 1),
        'confidence': confidence,
    }


BODY_TYPE_ALIASES = {
    'emission nebula': 'Nebula',
    'planetary nebula': 'Nebula',
    'cometary globule': 'Nebula',
    'supernova remnant': 'Nebula',
    'open star cluster': 'Star Cluster',
    'globular cluster': 'Star Cluster',
    'galaxy': 'Galaxy',
    'planet': 'Planet',
    'star': 'Star',
    'nebula': 'Nebula',
    'star cluster': 'Star Cluster',
    'moon': 'Planet',
    'natural satellite': 'Planet',
    'comet': 'Planet',
}


def assess_visibility(body_type, bortle_class):
    normalized = BODY_TYPE_ALIASES.get(body_type.lower(), body_type)
    thresholds = VISIBILITY_THRESHOLDS.get(normalized, VISIBILITY_THRESHOLDS['default'])
    if bortle_class <= thresholds['naked_eye']:
        return 'naked_eye'
    elif bortle_class <= thresholds['binoculars']:
        return 'binoculars'
    elif bortle_class <= thresholds['telescope']:
        return 'telescope'
    return 'not_visible'


# --- Main ---

BASE_URL = os.environ.get('STARGAZER_BASE_URL', 'http://localhost:8000').rstrip('/')

args = json.loads(sys.argv[1])

if 'address' in args and args['address']:
    geo = geocode_address(args['address'])
    lat = geo['lat']
    lon = geo['lon']
    location_name = geo['display_name']
elif 'latitude' in args and 'longitude' in args:
    lat = args['latitude']
    lon = args['longitude']
    location_name = f'{lat}, {lon}'
else:
    print(json.dumps({'error': 'Provide either an address or latitude/longitude'}))
    sys.exit(1)

# Get light pollution data
bortle = get_bortle_class(lat, lon)

# Get celestial bodies from local API
response = urllib.request.urlopen(f'{BASE_URL}/api/celestial-bodies/')
bodies = json.loads(response.read())

results = []
for body in bodies:
    ra = parse_ra(body['right_ascension'])
    dec = parse_dec(body['declination'])
    if ra is None or dec is None:
        continue
    alt, az = ra_dec_to_alt_az(ra, dec, lat, lon)
    above_horizon = alt > 0

    # Assess visibility based on light pollution
    visibility = assess_visibility(body['body_type'], bortle['bortle_class'])

    # Fist trick: one closed fist at arm's length covers ~10 degrees of sky
    fists = round(alt / 10, 1) if above_horizon else None
    fists_label = f"About {fists:.0f} fist{'s' if fists != 1 else ''} above the horizon" if fists and fists >= 1 else "Just above the horizon" if above_horizon else None

    results.append({
        'name': body['name'],
        'body_type': body['body_type'],
        'altitude': round(alt),
        'azimuth': round(az),
        'direction': az_to_direction(az),
        'above_horizon': above_horizon,
        'fists_above_horizon': fists,
        'fists_label': fists_label,
        'visibility': visibility if above_horizon else 'below_horizon',
        'visibility_label': VISIBILITY_LABELS.get(visibility, '') if above_horizon else 'Below the horizon',
        'apod_image': body.get('apod_image'),
        'apod_title': body.get('apod_title'),
    })

results.sort(key=lambda x: x['altitude'], reverse=True)
print(json.dumps({
    'location': location_name,
    'latitude': lat,
    'longitude': lon,
    'bortle': bortle,
    'bodies': results,
}))
