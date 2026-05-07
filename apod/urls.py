from django.urls import path
from .views import ApodListView, ApodDetailView, CelestialBodyListView, CollectionListView, visibility_view
from .chat import chat_view
from .tool_views import (
    get_celestial_bodies_view,
    get_todays_apod_view,
    get_visible_tonight_view,
    lookup_simbad_view,
    lookup_jpl_horizons_view,
)

urlpatterns = [
    path('apods/', ApodListView.as_view(), name='apod-list'),
    path('apods/<str:date>/', ApodDetailView.as_view(), name='apod-detail'),
    path('celestial-bodies/', CelestialBodyListView.as_view(), name='celestial-body-list'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('visibility/', visibility_view, name='visibility'),
    path('chat/', chat_view, name='astrid-chat'),
    # Tool execution endpoints - called by Vellum's hosted workflow runner
    path('tools/get_celestial_bodies/', get_celestial_bodies_view, name='tool-get-celestial-bodies'),
    path('tools/get_todays_apod/', get_todays_apod_view, name='tool-get-todays-apod'),
    path('tools/get_visible_tonight/', get_visible_tonight_view, name='tool-get-visible-tonight'),
    path('tools/lookup_simbad/', lookup_simbad_view, name='tool-lookup-simbad'),
    path('tools/lookup_jpl_horizons/', lookup_jpl_horizons_view, name='tool-lookup-jpl-horizons'),
]
