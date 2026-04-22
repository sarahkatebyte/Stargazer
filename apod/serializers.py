from rest_framework import serializers
from .models import Apod, CelestialBody, Collection


class ApodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apod
        fields = [
            'id',
            'date',
            'title',
            'explanation',
            'url',
            'hdurl',
            'media_type',
            'copyright',
            'created_at',
        ]


class CelestialBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = CelestialBody
        fields = [
            'id',
            'name',
            'body_type',
            'right_ascension',
            'declination',
            'description',
        ]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = [
            'id',
            'apod',
            'celestial_body',
            'collected_at',
        ]
