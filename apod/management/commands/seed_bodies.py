from django.core.management.base import BaseCommand
from apod.models import CelestialBody

BODIES = [
    {
        "name": "Jupiter",
        "body_type": "Planet",
        "right_ascension": "18h 00m 00s",
        "declination": "-23° 00' 00\"",
        "description": "The largest planet in the Solar System, a gas giant with iconic bands and the Great Red Spot.",
    },
    {
        "name": "Saturn",
        "body_type": "Planet",
        "right_ascension": "21h 00m 00s",
        "declination": "-18° 00' 00\"",
        "description": "The ringed gas giant, sixth planet from the Sun.",
    },
    {
        "name": "Mars",
        "body_type": "Planet",
        "right_ascension": "05h 00m 00s",
        "declination": "+25° 00' 00\"",
        "description": "The Red Planet, fourth from the Sun, with the largest volcano in the Solar System.",
    },
    {
        "name": "Sirius",
        "body_type": "Star",
        "right_ascension": "06h 45m 00s",
        "declination": "-16° 00' 00\"",
        "description": "The brightest star in the night sky, part of the constellation Canis Major.",
    },
    {
        "name": "Betelgeuse",
        "body_type": "Star",
        "right_ascension": "05h 55m 00s",
        "declination": "+07° 00' 00\"",
        "description": "A red supergiant in Orion, one of the largest and most luminous stars visible to the naked eye.",
    },
    {
        "name": "Polaris",
        "body_type": "Star",
        "right_ascension": "02h 31m 00s",
        "declination": "+89° 00' 00\"",
        "description": "The North Star, located almost directly above Earth's north pole.",
    },
    {
        "name": "Orion Nebula",
        "body_type": "Nebula",
        "right_ascension": "05h 35m 00s",
        "declination": "-05° 00' 00\"",
        "description": "A stellar nursery 1,344 light years away, one of the most photographed objects in the night sky.",
    },
    {
        "name": "Crab Nebula",
        "body_type": "Nebula",
        "right_ascension": "05h 34m 00s",
        "declination": "+22° 00' 00\"",
        "description": "The remnant of a supernova explosion observed in 1054 AD.",
    },
    {
        "name": "Pillars of Creation",
        "body_type": "Nebula",
        "right_ascension": "18h 18m 00s",
        "declination": "-13° 00' 00\"",
        "description": "Towering columns of gas and dust in the Eagle Nebula, made famous by the Hubble Space Telescope.",
    },
    {
        "name": "Andromeda Galaxy",
        "body_type": "Galaxy",
        "right_ascension": "00h 42m 00s",
        "declination": "+41° 00' 00\"",
        "description": "The nearest large galaxy to the Milky Way, visible to the naked eye from dark sky locations.",
    },
    {
        "name": "Triangulum Galaxy",
        "body_type": "Galaxy",
        "right_ascension": "01h 33m 00s",
        "declination": "+30° 00' 00\"",
        "description": "The third largest galaxy in the Local Group, about 2.73 million light years away.",
    },
    {
        "name": "Pleiades",
        "body_type": "Star Cluster",
        "right_ascension": "03h 47m 00s",
        "declination": "+24° 00' 00\"",
        "description": "An open star cluster containing middle-aged hot B-type stars, known as the Seven Sisters.",
    },
]

class Command(BaseCommand):
    help = 'Seeds the database with well-known celestial bodies'

    def handle(self, *args, **kwargs):
        created_count = 0
        for body in BODIES:
            _, created = CelestialBody.objects.get_or_create(
                name=body["name"],
                defaults=body
            )
            if created:
                created_count += 1
                self.stdout.write(f"Added: {body['name']}")
            else:
                self.stdout.write(f"Skipped (already exists): {body['name']}")

        self.stdout.write(f"\nDone — {created_count} new bodies added.")
