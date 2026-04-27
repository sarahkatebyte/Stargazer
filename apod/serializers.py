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
    apod_image = serializers.SerializerMethodField()
    apod_title = serializers.SerializerMethodField()

    class Meta:
        model = CelestialBody
        fields = [
            'id',
            'name',
            'body_type',
            'right_ascension',
            'declination',
            'description',
            'apod_image',
            'apod_title',
        ]

    def get_apod_image(self, obj):
        """Get the most recent APOD image URL for this body."""
        latest = obj.collection_set.select_related('apod').order_by('-apod__date').first()
        if latest:
            return latest.apod.url
        return None

    def get_apod_title(self, obj):
        """Get the most recent APOD title for this body."""
        latest = obj.collection_set.select_related('apod').order_by('-apod__date').first()
        if latest:
            return latest.apod.title
        return None


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = [
            'id',
            'apod',
            'celestial_body',
            'collected_at',
        ]
