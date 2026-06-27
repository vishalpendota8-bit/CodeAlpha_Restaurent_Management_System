from decimal import Decimal

from django.test import TestCase

from apps.menu.models import Category, MenuItem

from . import services
from .models import Ingredient, InventoryLog, Recipe


class InventoryServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Mains")
        self.burger = MenuItem.objects.create(
            category=category, name="Burger", price=Decimal("9.50")
        )
        self.bun = Ingredient.objects.create(
            name="Bun", quantity=Decimal("10"), unit="pcs", minimum_stock=Decimal("3")
        )
        self.patty = Ingredient.objects.create(
            name="Patty", quantity=Decimal("5"), unit="pcs", minimum_stock=Decimal("2")
        )
        Recipe.objects.create(
            menu_item=self.burger, ingredient=self.bun, quantity_required=Decimal("2")
        )
        Recipe.objects.create(
            menu_item=self.burger, ingredient=self.patty, quantity_required=Decimal("1")
        )

    def test_check_stock_passes_when_enough(self):
        services.check_stock([(self.burger, 3)])  # should not raise

    def test_check_stock_raises_when_short(self):
        with self.assertRaises(services.InsufficientStockError):
            services.check_stock([(self.burger, 6)])  # needs 12 buns, have 10

    def test_deduct_and_restore_round_trip(self):
        services.deduct_for_items([(self.burger, 2)], note="order #1")
        self.bun.refresh_from_db()
        self.patty.refresh_from_db()
        self.assertEqual(self.bun.quantity, Decimal("6"))
        self.assertEqual(self.patty.quantity, Decimal("3"))

        services.restore_for_items([(self.burger, 2)], note="cancel #1")
        self.bun.refresh_from_db()
        self.patty.refresh_from_db()
        self.assertEqual(self.bun.quantity, Decimal("10"))
        self.assertEqual(self.patty.quantity, Decimal("5"))
        self.assertEqual(InventoryLog.objects.count(), 4)

    def test_restock_increases_and_logs(self):
        services.restock(self.patty, Decimal("5"), note="delivery")
        self.patty.refresh_from_db()
        self.assertEqual(self.patty.quantity, Decimal("10"))
        self.assertTrue(
            InventoryLog.objects.filter(
                ingredient=self.patty, action=InventoryLog.Action.RESTOCK
            ).exists()
        )

    def test_low_stock_query(self):
        Ingredient.objects.create(
            name="Salt", quantity=Decimal("1"), unit="kg", minimum_stock=Decimal("2")
        )
        names = set(services.low_stock_ingredients().values_list("name", flat=True))
        self.assertEqual(names, {"Salt"})
