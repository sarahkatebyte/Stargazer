from django.shortcuts import render
from rest_framework import generics
from .models import Apod, CelestialBody, Collection
from .serializers import ApodSerializer, CelestialBodySerializer, CollectionSerializer

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
