from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api.models import Location, Address
from unittest.mock import patch


class CalculateDistanceTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("calculate_distance")
        self.valid_address_1 = "beverly center"
        self.valid_address_2 = "Central Park New York"
        self.nonexistent_address = "Nonexistent Address"

        # Mock data for locations
        self.location_1 = Location.objects.create(
            formatted_address="8500 Beverly Blvd, Los Angeles, CA 90048, USA",
            latitude=34.073620,
            longitude=-118.376068,
        )
        Address.objects.create(address=self.valid_address_1, location=self.location_1)

        self.location_2 = Location.objects.create(
            formatted_address="New York, NY, USA",
            latitude=40.785091,
            longitude=-73.968285,
        )
        Address.objects.create(address=self.valid_address_2, location=self.location_2)

    @patch("requests.get")
    def test_calculate_distance_successful(self, mock_get):
        mock_geocode_data = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "8500 Beverly Blvd, Los Angeles, CA 90048, USA",
                    "geometry": {"location": {"lat": 34.073620, "lng": -118.376068}},
                }
            ],
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_geocode_data

        response = self.client.get(
            self.url,
            {
                "start_address": self.valid_address_1,
                "end_address": self.valid_address_2,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("distance", response.data)
        self.assertIn("start_location", response.data)
        self.assertIn("end_location", response.data)

    @patch("requests.get")
    def test_calculate_distance_nonexistent_start_location(self, mock_get):
        mock_geocode_data = {"status": "ZERO_RESULTS", "results": []}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_geocode_data

        response = self.client.get(
            self.url,
            {
                "start_address": self.nonexistent_address,
                "end_address": self.valid_address_2,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "error": f"Could not fetch geocode for start address: {self.nonexistent_address.lower()}"
            },
        )

    @patch("requests.get")
    def test_calculate_distance_nonexistent_end_location(self, mock_get):
        mock_geocode_data = {"status": "ZERO_RESULTS", "results": []}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_geocode_data

        response = self.client.get(
            self.url,
            {
                "start_address": self.valid_address_1,
                "end_address": self.nonexistent_address,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "error": f"Could not fetch geocode for end address: {self.nonexistent_address.lower()}"
            },
        )

    def test_calculate_distance_missing_start_address(self):
        response = self.client.get(
            self.url, {"start_address": "", "end_address": self.valid_address_2}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"error": "Both start_address and end_address are required"}
        )

    def test_calculate_distance_missing_end_address(self):
        response = self.client.get(
            self.url, {"start_address": self.valid_address_1, "end_address": ""}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"error": "Both start_address and end_address are required"}
        )

    def test_calculate_distance_identical_locations(self):
        response = self.client.get(
            self.url,
            {
                "start_address": self.valid_address_1,
                "end_address": self.valid_address_1,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"error": "Both of these places have same address"}
        )

    def tearDown(self):
        Location.objects.all().delete()
        Address.objects.all().delete()
