from django.urls import path
from .views import ApodListView, ApodDetailView, CelestialBodyListView, CollectionListView, visibility_view
from .chat import chat_view
import os
from django.http import JsonResponse

def health_view(request):
    return JsonResponse({
        'status': 'ok',
        'anthropic_key_set': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'anthropic_key_prefix': os.environ.get('ANTHROPIC_API_KEY', '')[:8] or 'EMPTY',
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
    })

urlpatterns = [
    path('health/', health_view, name='health'),
    path('apods/', ApodListView.as_view(), name='apod-list'),
    path('apods/<str:date>/', ApodDetailView.as_view(), name='apod-detail'),
    path('celestial-bodies/', CelestialBodyListView.as_view(), name='celestial-body-list'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('visibility/', visibility_view, name='visibility'),
    path('chat/', chat_view, name='astrid-chat'),
]
