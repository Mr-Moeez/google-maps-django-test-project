from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api.models import Location, Address
from unittest.mock import patch
import os


class GetGeocodeTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("get_geocode")
        self.valid_address = "Devsinc"
        self.invalid_address = ""
        self.mock_geocode_data = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Plot B, 281 Ghazi Rd, Khuda Buksh Colony KB Society, Lahore, Punjab, Pakistan",
                    "geometry": {"location": {"lat": 37.4224764, "lng": -122.0842499}},
                }
            ],
        }

    @patch("requests.get")
    def test_get_geocode_successful(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_geocode_data

        response = self.client.get(self.url, {"address": self.valid_address})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("latitude", response.data)
        self.assertIn("longitude", response.data)
        self.assertIn("formatted_address", response.data)

    @patch("requests.get")
    def test_get_geocode_existing_location(self, mock_get):
        location = Location.objects.create(
            formatted_address=self.mock_geocode_data["results"][0]["formatted_address"],
            latitude=self.mock_geocode_data["results"][0]["geometry"]["location"][
                "lat"
            ],
            longitude=self.mock_geocode_data["results"][0]["geometry"]["location"][
                "lng"
            ],
        )
        Address.objects.create(address=self.valid_address, location=location)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_geocode_data

        response = self.client.get(self.url, {"address": self.valid_address})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(Address.objects.count(), 1)

    def test_get_geocode_no_address(self):
        response = self.client.get(self.url, {"address": self.invalid_address})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Address is required"})

    @patch("requests.get")
    def test_get_geocode_api_failure(self, mock_get):
        mock_get.return_value.status_code = 400
        mock_get.return_value.json.return_value = {"status": "INVALID_REQUEST"}

        response = self.client.get(self.url, {"address": self.valid_address})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("requests.get")
    def test_get_geocode_api_invalid_response(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ZERO_RESULTS"}

        response = self.client.get(self.url, {"address": self.valid_address})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch.dict(os.environ, {"MAP_API_KEY": "", "GOOGLE_MAP_URL": ""})
    def test_get_geocode_env_variables_missing(self):
        response = self.client.get(self.url, {"address": self.valid_address})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Environment variables are not set"})

    def tearDown(self):
        Location.objects.all().delete()
        Address.objects.all().delete()
