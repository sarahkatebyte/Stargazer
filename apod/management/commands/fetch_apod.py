import os
import requests
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from apod.models import Apod
from apod.agents.astronomy_agent import analyze_apod

load_dotenv()

class Command(BaseCommand):
    help = 'Fetches the Astronomy Picture of the Day from NASA'

    def add_arguments(self, parser):
        parser.add_argument('date', nargs='?', help='Date in YYYY-MM-DD format (defaults to today)')

    def handle(self, *args, **kwargs):
        api_key = os.getenv('NASA_API_KEY')
        date = kwargs.get('date')
        url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
        if date:
            url += f'&date={date}'
        response = requests.get(url)
        self.stdout.write(f"Status: {response.status_code}")
        self.stdout.write(f"Body: {response.text}")
        data = response.json()
        apod_obj, created = Apod.objects.get_or_create(
            date=data['date'],
            defaults={
                'title': data['title'],
                'explanation': data['explanation'],
                'url': data['url'],
                'hdurl': data.get('hdurl'),
                'media_type': data['media_type'],
                'copyright': data.get('copyright'),
            }
        )

        self.stdout.write(f"Fetched: {data['date']} - {data['title']}")

        if created:
            self.stdout.write("Running astronomy agent...")
            analyze_apod(apod_obj)
            self.stdout.write("Agent complete.")