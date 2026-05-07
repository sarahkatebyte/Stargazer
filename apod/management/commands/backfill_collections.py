"""
backfill_collections — link existing CelestialBodies to APODs by title/explanation matching.

Scans APOD titles and explanations for the names of seeded celestial bodies and
creates Collection entries where a match is found. No API calls — pure text matching.

Matching strategy: full body name only (avoids false positives from partial matches).
Common aliases are defined below for bodies with multiple known names.

Usage:
    python manage.py backfill_collections             # dry run (shows matches, no writes)
    python manage.py backfill_collections --save      # actually create Collection entries
    python manage.py backfill_collections --save --limit 100  # cap at 100 new collections
"""

from django.core.management.base import BaseCommand
from apod.models import Apod, CelestialBody, Collection

# Additional aliases for bodies whose APOD titles use different names
ALIASES = {
    'Milky Way':          ['Milky Way'],
    'Jupiter':            ['Jupiter'],
    'Saturn':             ['Saturn'],
    'Mars':               ['Mars'],
    'Venus':              ['Venus'],
    'Moon':               ['Moon'],
    'Titan':              ['Titan'],
    'Sirius':             ['Sirius'],
    'Betelgeuse':         ['Betelgeuse'],
    'Polaris':            ['Polaris', 'North Star'],
    'Orion Nebula':       ['Orion Nebula'],
    'Crab Nebula':        ['Crab Nebula'],          # M1 too ambiguous — matches M13, M100 etc.
    'Andromeda Galaxy':   ['Andromeda', 'M31:'],    # "M31:" with colon avoids M31x false positives
    'Triangulum Galaxy':  ['Triangulum'],
    'Pleiades':           ['Pleiades', 'Seven Sisters'],
    'Pillars of Creation':['Pillars of Creation'],
    'Comet C/2025 R3 (PanSTARRS)': ['C/2025 R3', 'PanSTARRS R3', 'Comet R3'],
}


class Command(BaseCommand):
    help = 'Link existing CelestialBodies to APODs via name matching (no API calls)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            action='store_true',
            help='Actually create Collection entries (default is dry run)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Max number of new Collection entries to create',
        )

    def handle(self, *args, **options):
        save = options['save']
        limit = options['limit']

        bodies = CelestialBody.objects.all()
        apods = Apod.objects.all()

        self.stdout.write(
            f"{'[DRY RUN] ' if not save else ''}"
            f"Scanning {bodies.count()} bodies against {apods.count()} APODs...\n"
        )

        created_count = 0
        already_linked = 0

        for body in bodies:
            # Get search terms: full name + any defined aliases
            search_terms = ALIASES.get(body.name, [body.name])

            # Find APODs whose TITLE contains any of the search terms (title-only avoids
            # false positives from bodies mentioned incidentally in explanations)
            matching_apods = []
            for apod in apods:
                title = apod.title.lower()
                if any(term.lower() in title for term in search_terms):
                    matching_apods.append(apod)

            # Sort by date descending
            matching_apods.sort(key=lambda a: a.date, reverse=True)

            for apod in matching_apods:
                if Collection.objects.filter(apod=apod, celestial_body=body).exists():
                    already_linked += 1
                    continue

                self.stdout.write(
                    f"  {'[WOULD CREATE]' if not save else '[CREATING]'} "
                    f"{body.name} ↔ {apod.date} ({apod.title[:70]})"
                )

                if save:
                    Collection.objects.create(apod=apod, celestial_body=body)
                    created_count += 1

                    if limit and created_count >= limit:
                        self.stdout.write(self.style.WARNING(f"\nLimit of {limit} reached. Stopping."))
                        self._summary(created_count, already_linked, save)
                        return
                else:
                    created_count += 1

        self._summary(created_count, already_linked, save)

    def _summary(self, created, skipped, save):
        self.stdout.write('')
        if save:
            self.stdout.write(self.style.SUCCESS(f"Done. Created {created} new Collection entries."))
        else:
            self.stdout.write(self.style.WARNING(
                f"Dry run complete. Would create {created} new Collection entries. "
                f"Run with --save to apply."
            ))
        self.stdout.write(f"Already linked (skipped): {skipped}")
