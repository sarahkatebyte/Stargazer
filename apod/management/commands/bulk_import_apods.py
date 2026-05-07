import os
import time
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from apod.models import Apod

load_dotenv()


def date_chunks(start: date, end: date, chunk_days: int = 90):
    """Yield (start, end) tuples in chunks of chunk_days."""
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


class Command(BaseCommand):
    help = 'Bulk imports APODs from NASA API in chunks to avoid rate limits'

    def add_arguments(self, parser):
        parser.add_argument('--start', default='2022-01-01', help='Start date YYYY-MM-DD')
        parser.add_argument('--end', default=None, help='End date YYYY-MM-DD (defaults to today)')
        parser.add_argument('--chunk-days', type=int, default=90, help='Days per API request (default 90)')
        parser.add_argument('--delay', type=float, default=1.0, help='Seconds to wait between requests (default 1)')

    def handle(self, *args, **kwargs):
        api_key = os.getenv('NASA_API_KEY')
        start = date.fromisoformat(kwargs['start'])
        end = date.fromisoformat(kwargs['end']) if kwargs['end'] else date.today()
        chunk_days = kwargs['chunk_days']
        delay = kwargs['delay']

        chunks = list(date_chunks(start, end, chunk_days))
        self.stdout.write(
            f'Fetching APODs {start} → {end} in {len(chunks)} chunks of {chunk_days} days...\n'
        )

        total_created = 0
        total_skipped = 0

        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            self.stdout.write(f'[{i}/{len(chunks)}] {chunk_start} → {chunk_end}', ending=' ')

            url = (
                f'https://api.nasa.gov/planetary/apod'
                f'?api_key={api_key}'
                f'&start_date={chunk_start}'
                f'&end_date={chunk_end}'
                f'&thumbs=true'
            )

            try:
                response = requests.get(url, timeout=60)
            except requests.exceptions.Timeout:
                self.stdout.write(self.style.ERROR('TIMEOUT — skipping chunk'))
                continue

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'ERROR {response.status_code} — skipping chunk'))
                continue

            data = response.json()
            created_count = 0
            skipped_count = 0

            for item in data:
                if item.get('media_type') != 'image':
                    skipped_count += 1
                    continue

                _, created = Apod.objects.get_or_create(
                    date=item['date'],
                    defaults={
                        'title': item.get('title', ''),
                        'explanation': item.get('explanation', ''),
                        'url': item.get('url', ''),
                        'hdurl': item.get('hdurl'),
                        'media_type': item.get('media_type', 'image'),
                        'copyright': item.get('copyright'),
                    }
                )
                if created:
                    created_count += 1

            total_created += created_count
            total_skipped += skipped_count
            self.stdout.write(f'→ {created_count} new, {skipped_count} videos skipped')

            if i < len(chunks):
                time.sleep(delay)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done — {total_created} new APODs saved, {total_skipped} videos skipped total.'
        ))
