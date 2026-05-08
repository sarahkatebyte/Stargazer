"""
Test-only settings for Stargazer.

Overrides the database to use SQLite in-memory so tests can run without
a Postgres connection or CREATE DATABASE permissions.

Usage:
    python manage.py test apod --settings=stargazer.test_settings
"""

from .settings import *  # noqa: F401, F403 — intentional wildcard import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
