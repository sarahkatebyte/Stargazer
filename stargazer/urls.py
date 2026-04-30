from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apod.urls')),
    # Catch-all: serve the React app's index.html for any non-API route.
    # The WHY: React Router handles client-side navigation. When a user
    # hits /explore or refreshes the page, the browser asks Django for
    # that path. Django doesn't have a view for it - React does. So we
    # serve index.html and let React's router take over.
    re_path(r'^(?!api/|admin/|assets/).*$', TemplateView.as_view(template_name='index.html')),
]
