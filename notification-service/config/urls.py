from django.contrib import admin
from django.urls import path, include
from notifications.views import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path("health/", health),
    path("api/notifications/", include("notifications.urls")),
]
