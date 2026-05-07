"""
Management command: refresh_planet_coords

Calls the lookup_jpl_horizons skill script for each solar system body
in the database and updates its right_ascension and declination with
today's actual coordinates.

Usage:
    python manage.py refresh_planet_coords
"""

import json
import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand

from apod.models import CelestialBody

SOLAR_SYSTEM_TYPES = {'Planet', 'planet', 'Moon', 'moon', 'Natural Satellite',
                       'natural satellite', 'Comet', 'comet', 'Dwarf Planet'}

SCRIPT = Path(__file__).resolve().parents[4] / 'skill' / 'scripts' / 'lookup_jpl_horizons.py'


def fetch_jpl(name):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), json.dumps({'name': name})],
        capture_output=True, text=True, timeout=30,
        cwd=str(SCRIPT.parent),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    outer = json.loads(result.stdout)
    # Script nests JPL data under 'jpl_horizons'
    jpl = outer.get('jpl_horizons', {})
    if not jpl.get('found'):
        raise RuntimeError(jpl.get('error', 'not found in JPL'))
    return jpl


class Command(BaseCommand):
    help = 'Refresh RA/Dec coordinates for solar system bodies from JPL Horizons'

    def handle(self, *args, **options):
        bodies = CelestialBody.objects.filter(body_type__in=SOLAR_SYSTEM_TYPES)
        self.stdout.write(f'Found {bodies.count()} solar system bodies to update.')

        updated, failed = 0, 0
        for body in bodies:
            try:
                data = fetch_jpl(body.name)
                ra = data.get('ra_hms')
                dec = data.get('dec_dms')
                if not ra or not dec:
                    self.stdout.write(self.style.WARNING(
                        f'  {body.name}: no coordinates returned - skipping'
                    ))
                    failed += 1
                    continue
                body.right_ascension = ra
                body.declination = dec
                body.save(update_fields=['right_ascension', 'declination'])
                self.stdout.write(self.style.SUCCESS(
                    f'  {body.name}: RA={body.right_ascension}  Dec={body.declination}'
                ))
                updated += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  {body.name}: FAILED - {e}'))
                failed += 1

        self.stdout.write(f'\nDone. Updated: {updated}  Failed: {failed}')
