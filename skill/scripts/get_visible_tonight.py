import sys
import json
import math
import urllib.request
from datetime import datetime, timezone

def parse_ra(ra):
    import re
    match = re.search(r'(\d+)h\s*(\d+)m', ra)
    if not match:
        return None
    return int(match.group(1)) + int(match.group(2)) / 60

def parse_dec(dec):
    import re
    match = re.search(r'([+-]?\d+)°', dec)
    if not match:
        return None
    return int(match.group(1))

def ra_dec_to_alt_az(ra_hours, dec_deg, lat, lon):
    now = datetime.now(timezone.utc)
    jd = (now.timestamp() / 86400.0) + 2440587.5
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    lst = (gmst + lon) % 360
    ha = lst - ra_hours * 15
    ra_rad = math.radians(ra_hours * 15)
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

args = json.loads(sys.argv[1])
lat = args['latitude']
lon = args['longitude']

response = urllib.request.urlopen('http://localhost:8000/api/celestial-bodies/')
bodies = json.loads(response.read())

results = []
for body in bodies:
    ra = parse_ra(body['right_ascension'])
    dec = parse_dec(body['declination'])
    if ra is None or dec is None:
        continue
    alt, az = ra_dec_to_alt_az(ra, dec, lat, lon)
    results.append({
        'name': body['name'],
        'body_type': body['body_type'],
        'altitude': round(alt),
        'azimuth': round(az),
        'direction': az_to_direction(az),
        'visible': alt > 0,
    })

results.sort(key=lambda x: x['altitude'], reverse=True)
print(json.dumps(results))
