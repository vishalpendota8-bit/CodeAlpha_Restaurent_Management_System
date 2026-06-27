from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import RestaurantTable


class TableTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager", password="pass12345", role=User.Role.MANAGER
        )
        RestaurantTable.objects.create(table_number=1, capacity=2)
        RestaurantTable.objects.create(
            table_number=2, capacity=6, status=RestaurantTable.Status.OCCUPIED
        )

    def test_available_endpoint_excludes_occupied(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get(reverse("tables:table-available"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        numbers = [t["table_number"] for t in response.data["results"]]
        self.assertIn(1, numbers)
        self.assertNotIn(2, numbers)

    def test_available_filters_by_guests(self):
        RestaurantTable.objects.create(table_number=3, capacity=8)
        self.client.force_authenticate(self.manager)
        response = self.client.get(
            reverse("tables:table-available"), {"guests": 5}
        )
        numbers = [t["table_number"] for t in response.data["results"]]
        self.assertEqual(numbers, [3])
