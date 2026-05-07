from django.apps import AppConfig


class ApodConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apod'

    def ready(self):
        """Seed celestial bodies on startup if the table is empty."""
        try:
            from django.db import connection
            # Only run after migrations have created the table
            if 'apod_celestialbody' in connection.introspection.table_names():
                from .models import CelestialBody
                if CelestialBody.objects.count() == 0:
                    from django.core.management import call_command
                    call_command('seed_bodies', verbosity=0)
        except Exception:
            pass  # Never block startup
