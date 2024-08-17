import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from ..models import Location, Address
from ..serializers import DistanceResponseSerializer
from ..utils import calculate_distance
import os
from dotenv import load_dotenv
import pdb


class CalculateDistanceView(GenericAPIView):
    """
    Calculates the distance between two locations based on their addresses.
    """
    serializer_class = DistanceResponseSerializer

    def get_or_create_location(self, address):
        load_dotenv()
        map_api_key = os.environ.get("MAP_API_KEY")
        url = os.environ.get("GOOGLE_MAP_URL")

        if not map_api_key or not url:
            return Response(
                {"error": "Environment variables are not set"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        existing_address = Address.objects.filter(address=address).first()
        if existing_address:
            return existing_address.location

        params = {"address": address, "key": map_api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Error fetching geocode: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = response.json()

        if data["status"] == "OK":
            location_data = data["results"][0]["geometry"]["location"]
            formatted_address = data["results"][0]["formatted_address"]

            existing_location = Location.objects.filter(
                formatted_address=formatted_address
            ).first()

            if existing_location:
                Address.objects.create(address=address, location=existing_location)
                return existing_location

            location = Location.objects.create(
                formatted_address=formatted_address,
                latitude=location_data["lat"],
                longitude=location_data["lng"],
            )
            Address.objects.create(address=address, location=location)
            return location
        else:
            return None

    def get(self, request, *args, **kwargs):
        start_address = request.GET.get("start_address")
        end_address = request.GET.get("end_address")

        if not start_address or not end_address:
            return Response(
                {"error": "Both start_address and end_address are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        start_address = start_address.lower()
        end_address = end_address.lower()

        start_location = self.get_or_create_location(start_address)
        if not start_location:
            return Response(
                {
                    "error": f"Could not fetch geocode for start address: {start_address}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        end_location = self.get_or_create_location(end_address)
        if not end_location:
            return Response(
                {"error": f"Could not fetch geocode for end address: {end_address}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if start_location.formatted_address == end_location.formatted_address:
            return Response(
                {"error": "Both of these places have same address"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        distance = calculate_distance(
            start_location.latitude,
            start_location.longitude,
            end_location.latitude,
            end_location.longitude,
        )
        data = {
            "start_location": start_address,
            "end_location": end_address,
            "distance": distance,
        }
        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)
