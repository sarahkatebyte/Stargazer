from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Apod, CelestialBody, Collection
from .serializers import ApodSerializer, CelestialBodySerializer, CollectionSerializer
from .light_pollution import get_bortle_class, assess_visibility

class ApodListView(generics.ListAPIView):
    queryset = Apod.objects.all().order_by('-date')
    serializer_class = ApodSerializer

class ApodDetailView(generics.RetrieveAPIView):
    queryset = Apod.objects.all()
    serializer_class = ApodSerializer
    lookup_field = 'date'

class CelestialBodyListView(generics.ListAPIView):
    queryset = CelestialBody.objects.all()
    serializer_class = CelestialBodySerializer

class CollectionListView(generics.ListAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


@api_view(['GET'])
def visibility_view(request):
    """
    Returns Bortle class and per-body visibility for a location.
    Query params: lat, lon (required)
    """
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')

    if not lat or not lon:
        return Response(
            {'error': 'lat and lon query parameters are required'},
            status=400,
        )

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return Response(
            {'error': 'lat and lon must be valid numbers'},
            status=400,
        )

    bortle = get_bortle_class(lat, lon)
    bodies = CelestialBody.objects.all()

    body_visibility = []
    for body in bodies:
        visibility = assess_visibility(body.body_type, bortle['bortle_class'])
        body_visibility.append({
            'name': body.name,
            'body_type': body.body_type,
            'visibility': visibility,
        })

    return Response({
        'bortle': bortle,
        'bodies': body_visibility,
    })
