from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Category, MenuItem


class MenuTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="manager", password="pass12345", role=User.Role.MANAGER
        )
        self.waiter = User.objects.create_user(
            username="waiter", password="pass12345", role=User.Role.WAITER
        )
        self.category = Category.objects.create(name="Mains")

    def test_waiter_can_read_menu(self):
        self.client.force_authenticate(self.waiter)
        response = self.client.get(reverse("menu:menuitem-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_waiter_cannot_create_item(self):
        self.client.force_authenticate(self.waiter)
        response = self.client.post(
            reverse("menu:menuitem-list"),
            {"category": self.category.id, "name": "Steak", "price": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_creates_item(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("menu:menuitem-list"),
            {"category": self.category.id, "name": "Steak", "price": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MenuItem.objects.filter(name="Steak").exists())

    def test_price_must_be_positive(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("menu:menuitem-list"),
            {"category": self.category.id, "name": "Free", "price": "0"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
