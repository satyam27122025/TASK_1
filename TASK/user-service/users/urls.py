from django.urls import path
from .views import register, login, profile, health

urlpatterns = [
    path("health/", health),
    path("register/", register),
    path("login/", login),
    path("profile/", profile),
]