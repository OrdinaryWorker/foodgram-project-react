
from django.contrib import admin
from django.urls import include, path

from .yasg import urlpatterns as yasg_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
]

urlpatterns += yasg_urls
