# api/serializers.py

from rest_framework import serializers
from .models import Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class DistanceResponseSerializer(serializers.Serializer):
    start_location = serializers.CharField()
    end_location = serializers.CharField()
    distance = serializers.FloatField()


