# api/urls.py

from django.urls import path
from .views import (
    CalculateDistanceView,
    GetGeocodeView,
)


urlpatterns = [
    path("geocode/", GetGeocodeView.as_view(), name="get_geocode"),
    path("distance/", CalculateDistanceView.as_view(), name="calculate_distance"),
]
