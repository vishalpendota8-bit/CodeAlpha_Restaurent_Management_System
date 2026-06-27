from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.tables.models import RestaurantTable

from .models import Reservation


class ReservationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="waiter", password="pass12345", role=User.Role.WAITER
        )
        self.client.force_authenticate(self.user)
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)
        self.when = timezone.now() + timezone.timedelta(days=1)

    def _payload(self, **overrides):
        data = {
            "customer_name": "Dana",
            "phone": "555-1000",
            "table": self.table.id,
            "reservation_time": self.when.isoformat(),
            "guests": 2,
        }
        data.update(overrides)
        return data

    def test_create_reservation_marks_table_reserved(self):
        response = self.client.post("/reservations/", self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, RestaurantTable.Status.RESERVED)

    def test_reject_when_over_capacity(self):
        response = self.client.post(
            "/reservations/", self._payload(guests=10), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_prevent_double_booking(self):
        self.client.post("/reservations/", self._payload(), format="json")
        response = self.client.post(
            "/reservations/",
            self._payload(customer_name="Eve", phone="555-2000"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_frees_table(self):
        create = self.client.post("/reservations/", self._payload(), format="json")
        reservation_id = create.data["id"]
        response = self.client.post(f"/reservations/{reservation_id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, RestaurantTable.Status.AVAILABLE)
        self.assertEqual(
            Reservation.objects.get(pk=reservation_id).status,
            Reservation.Status.CANCELLED,
        )
