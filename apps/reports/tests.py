from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.menu.models import Category, MenuItem
from apps.orders.models import Order, OrderItem
from apps.tables.models import RestaurantTable


class ReportTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager", password="pass12345", role=User.Role.MANAGER
        )
        self.client.force_authenticate(self.manager)

        category = Category.objects.create(name="Mains")
        self.burger = MenuItem.objects.create(
            category=category, name="Burger", price=Decimal("10.00")
        )
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)

        order = Order.objects.create(
            table=self.table,
            waiter=self.manager,
            status=Order.Status.COMPLETED,
            payment_status=Order.PaymentStatus.PAID,
            subtotal=Decimal("20.00"),
            tax=Decimal("2.00"),
            total=Decimal("22.00"),
        )
        OrderItem.objects.create(
            order=order, menu_item=self.burger, quantity=2, price=Decimal("10.00")
        )

    def test_daily_sales(self):
        response = self.client.get(reverse("reports:daily"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["revenue"]), Decimal("22.00"))
        self.assertEqual(response.data["orders"], 1)

    def test_monthly_sales(self):
        today = timezone.localdate()
        response = self.client.get(
            reverse("reports:monthly"), {"year": today.year, "month": today.month}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["revenue"]), Decimal("22.00"))

    def test_top_items(self):
        response = self.client.get(reverse("reports:top-items"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Burger")
        self.assertEqual(response.data[0]["quantity_sold"], 2)

    def test_low_stock_requires_manager(self):
        waiter = User.objects.create_user(
            username="w2", password="pass12345", role=User.Role.WAITER
        )
        self.client.force_authenticate(waiter)
        response = self.client.get(reverse("reports:low-stock"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
