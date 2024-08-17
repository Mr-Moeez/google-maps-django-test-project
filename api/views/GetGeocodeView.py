import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from ..models import Location, Address
from ..serializers import LocationSerializer
import os
from dotenv import load_dotenv


class GetGeocodeView(GenericAPIView):
    """
    Retrieves geocode information for a given address.
    """
    
    serializer_class = LocationSerializer

    def get(self, request, *args, **kwargs):
        load_dotenv()
        address = request.GET.get("address")

        if not address:
            return Response(
                {"error": "Address is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        address = address.lower()

        map_api_key = os.environ.get("MAP_API_KEY")
        url = os.environ.get("GOOGLE_MAP_URL")

        if not map_api_key or not url:
            return Response(
                {"error": "Environment variables are not set"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        params = {"address": address, "key": map_api_key}

        existing_address = Address.objects.filter(address=address).first()

        if existing_address:
            location = existing_address.location
            serializer = self.get_serializer(location)
            data = serializer.data
            return Response(data, status=status.HTTP_200_OK)

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
                serializer = self.get_serializer(existing_location)
                data = serializer.data
                return Response(data, status=status.HTTP_201_CREATED)
            location = Location.objects.create(
                formatted_address=formatted_address,
                latitude=location_data["lat"],
                longitude=location_data["lng"],
            )
            Address.objects.create(address=address, location=location)

            serializer = self.get_serializer(location)
            data = serializer.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": f"Geocode API error: {data['status']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
