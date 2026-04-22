import os
import requests
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from apod.models import Apod

load_dotenv()

class Command(BaseCommand):
    help = 'Bulk imports all APODs from NASA API'

    def add_arguments(self, parser):
        parser.add_argument('--start', default='1995-06-16', help='Start date YYYY-MM-DD')
        parser.add_argument('--end', default=None, help='End date YYYY-MM-DD (defaults to today)')

    def handle(self, *args, **kwargs):
        api_key = os.getenv('NASA_API_KEY')
        start = kwargs['start']
        end = kwargs['end']

        url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}&start_date={start}&thumbs=true'
        if end:
            url += f'&end_date={end}'

        self.stdout.write(f'Fetching APODs from {start}...')
        response = requests.get(url, timeout=120)

        if response.status_code != 200:
            self.stdout.write(f'Error: {response.status_code} — {response.text[:200]}')
            return

        data = response.json()
        self.stdout.write(f'Fetched {len(data)} APODs. Saving to database...')

        created_count = 0
        skipped_count = 0

        for item in data:
            # Only save image APODs, skip videos
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

        self.stdout.write(f'Done — {created_count} new APODs saved, {skipped_count} videos skipped.')
