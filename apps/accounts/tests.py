from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthTests(APITestCase):
    def test_register_creates_user(self):
        url = reverse("accounts:register")
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "StrongPass123",
            "password2": "StrongPass123",
            "role": User.Role.WAITER,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_register_password_mismatch(self):
        url = reverse("accounts:register")
        payload = {
            "username": "bob",
            "password": "StrongPass123",
            "password2": "Different123",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_tokens(self):
        User.objects.create_user(username="carol", password="StrongPass123")
        url = reverse("accounts:login")
        response = self.client.post(
            url, {"username": "carol", "password": "StrongPass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "carol")

    def test_me_requires_authentication(self):
        url = reverse("accounts:me")
        self.assertEqual(
            self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED
        )
