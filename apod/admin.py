from django.contrib import admin
from .models import Apod, CelestialBody, Collection


admin.site.register(Apod)
admin.site.register(CelestialBody)
admin.site.register(Collection)
