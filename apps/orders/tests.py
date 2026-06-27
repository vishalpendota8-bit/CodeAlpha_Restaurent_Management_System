from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.inventory.models import Ingredient, Recipe
from apps.menu.models import Category, MenuItem
from apps.tables.models import RestaurantTable

from .models import Order


class OrderFlowTests(APITestCase):
    def setUp(self):
        self.waiter = User.objects.create_user(
            username="waiter", password="pass12345", role=User.Role.WAITER
        )
        self.client.force_authenticate(self.waiter)

        category = Category.objects.create(name="Mains")
        self.burger = MenuItem.objects.create(
            category=category, name="Burger", price=Decimal("10.00")
        )
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)

        self.bun = Ingredient.objects.create(
            name="Bun", quantity=Decimal("10"), unit="pcs", minimum_stock=Decimal("2")
        )
        Recipe.objects.create(
            menu_item=self.burger, ingredient=self.bun, quantity_required=Decimal("2")
        )

    def _place(self, quantity=2):
        return self.client.post(
            reverse("orders:order-list"),
            {
                "table": self.table.id,
                "items": [{"menu_item": self.burger.id, "quantity": quantity}],
            },
            format="json",
        )

    def test_place_order_calculates_totals_and_deducts_stock(self):
        response = self._place(quantity=2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # subtotal 20.00, tax 10% = 2.00, total 22.00
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("20.00"))
        self.assertEqual(Decimal(response.data["tax"]), Decimal("2.00"))
        self.assertEqual(Decimal(response.data["total"]), Decimal("22.00"))

        self.bun.refresh_from_db()
        self.assertEqual(self.bun.quantity, Decimal("6"))  # 10 - (2*2)

        self.table.refresh_from_db()
        self.assertEqual(self.table.status, RestaurantTable.Status.OCCUPIED)

    def test_order_blocked_when_stock_insufficient(self):
        response = self._place(quantity=6)  # needs 12 buns, have 10
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("shortages", response.data)
        self.bun.refresh_from_db()
        self.assertEqual(self.bun.quantity, Decimal("10"))  # untouched

    def test_order_blocked_for_unavailable_item(self):
        self.burger.available = False
        self.burger.save(update_fields=["available"])
        response = self._place()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_order_frees_table_and_marks_paid(self):
        order_id = self._place().data["id"]
        response = self.client.post(
            reverse("orders:order-complete", args=[order_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.COMPLETED)
        self.assertEqual(response.data["payment_status"], Order.PaymentStatus.PAID)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, RestaurantTable.Status.AVAILABLE)

    def test_cancel_order_restores_stock_and_frees_table(self):
        order_id = self._place(quantity=2).data["id"]
        response = self.client.post(
            reverse("orders:order-cancel", args=[order_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.CANCELLED)
        self.bun.refresh_from_db()
        self.assertEqual(self.bun.quantity, Decimal("10"))  # restored
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, RestaurantTable.Status.AVAILABLE)

    def test_cannot_cancel_completed_order(self):
        order_id = self._place().data["id"]
        self.client.post(reverse("orders:order-complete", args=[order_id]))
        response = self.client.post(
            reverse("orders:order-cancel", args=[order_id])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
