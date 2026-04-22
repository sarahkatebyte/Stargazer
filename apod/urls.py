from django.urls import path
from .views import ApodListView, ApodDetailView, CelestialBodyListView, CollectionListView

urlpatterns = [
    path('apods/', ApodListView.as_view(), name='apod-list'),
    path('apods/<str:date>/', ApodDetailView.as_view(), name='apod-detail'),
    path('celestial-bodies/', CelestialBodyListView.as_view(), name='celestial-body-list'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
]
