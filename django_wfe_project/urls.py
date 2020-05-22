from django.contrib import admin
from django.urls import path, include

from django_wfe_integration.urls import urlpatterns as integration_patterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(integration_patterns)),
    path('api/wfe', include("django_wfe.urls", namespace="django_wfe")),
]
