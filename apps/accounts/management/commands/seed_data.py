"""Populate the database with realistic demo data.

Usage:
    python manage.py seed_data
    python manage.py seed_data --flush   # wipe demo tables first
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.inventory.models import Ingredient, Recipe
from apps.menu.models import Category, MenuItem
from apps.tables.models import RestaurantTable


class Command(BaseCommand):
    help = "Seed the database with demo users, menu, tables and inventory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing demo data...")
            Recipe.objects.all().delete()
            MenuItem.objects.all().delete()
            Category.objects.all().delete()
            Ingredient.objects.all().delete()
            RestaurantTable.objects.all().delete()

        self._seed_users()
        categories = self._seed_menu()
        self._seed_tables()
        self._seed_inventory(categories)

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
        self.stdout.write(
            "Logins (password 'password123'): admin / manager / waiter"
        )

    def _seed_users(self):
        defaults = [
            ("admin", User.Role.ADMIN, True),
            ("manager", User.Role.MANAGER, False),
            ("waiter", User.Role.WAITER, False),
        ]
        for username, role, is_super in defaults:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": role,
                    "email": f"{username}@example.com",
                    "is_staff": role in {User.Role.ADMIN, User.Role.MANAGER},
                    "is_superuser": is_super,
                },
            )
            if created:
                user.set_password("password123")
                user.save()
                self.stdout.write(f"  user: {username} ({role})")

    def _seed_menu(self):
        data = {
            "Starters": [
                ("Garlic Bread", "Toasted bread with garlic butter", "5.50"),
                ("Soup of the Day", "Chef's daily soup", "6.00"),
            ],
            "Mains": [
                ("Classic Burger", "Beef patty, cheese, lettuce, bun", "12.00"),
                ("Margherita Pizza", "Tomato, mozzarella, basil", "11.00"),
                ("Grilled Salmon", "Salmon fillet with veg", "16.50"),
            ],
            "Desserts": [
                ("Cheesecake", "New York style cheesecake", "7.00"),
                ("Ice Cream", "Three scoops", "4.50"),
            ],
            "Drinks": [
                ("Lemonade", "Fresh squeezed", "3.50"),
                ("Coffee", "Single origin", "3.00"),
            ],
        }
        categories = {}
        for category_name, items in data.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            categories[category_name] = category
            for name, description, price in items:
                MenuItem.objects.get_or_create(
                    category=category,
                    name=name,
                    defaults={
                        "description": description,
                        "price": Decimal(price),
                        "available": True,
                    },
                )
        self.stdout.write(f"  menu: {MenuItem.objects.count()} items")
        return categories

    def _seed_tables(self):
        for number, capacity in [(1, 2), (2, 2), (3, 4), (4, 4), (5, 6), (6, 8)]:
            RestaurantTable.objects.get_or_create(
                table_number=number, defaults={"capacity": capacity}
            )
        self.stdout.write(f"  tables: {RestaurantTable.objects.count()}")

    def _seed_inventory(self, categories):
        ingredients = {
            "Beef Patty": ("40", "pcs", "10"),
            "Burger Bun": ("40", "pcs", "10"),
            "Cheese Slice": ("60", "pcs", "15"),
            "Lettuce": ("5", "kg", "1"),
            "Pizza Dough": ("30", "pcs", "8"),
            "Tomato Sauce": ("8", "l", "2"),
            "Mozzarella": ("6", "kg", "2"),
            "Salmon Fillet": ("20", "pcs", "5"),
            "Coffee Beans": ("3", "kg", "1"),
            "Lemon": ("50", "pcs", "10"),
        }
        objs = {}
        for name, (qty, unit, minimum) in ingredients.items():
            obj, _ = Ingredient.objects.get_or_create(
                name=name,
                defaults={
                    "quantity": Decimal(qty),
                    "unit": unit,
                    "minimum_stock": Decimal(minimum),
                },
            )
            objs[name] = obj

        recipes = {
            "Classic Burger": [
                ("Beef Patty", "1"),
                ("Burger Bun", "1"),
                ("Cheese Slice", "1"),
                ("Lettuce", "0.05"),
            ],
            "Margherita Pizza": [
                ("Pizza Dough", "1"),
                ("Tomato Sauce", "0.15"),
                ("Mozzarella", "0.2"),
            ],
            "Grilled Salmon": [("Salmon Fillet", "1")],
            "Coffee": [("Coffee Beans", "0.02")],
            "Lemonade": [("Lemon", "2")],
        }
        for item_name, components in recipes.items():
            menu_item = MenuItem.objects.filter(name=item_name).first()
            if not menu_item:
                continue
            for ingredient_name, amount in components:
                Recipe.objects.get_or_create(
                    menu_item=menu_item,
                    ingredient=objs[ingredient_name],
                    defaults={"quantity_required": Decimal(amount)},
                )
        self.stdout.write(
            f"  inventory: {Ingredient.objects.count()} ingredients, "
            f"{Recipe.objects.count()} recipes"
        )
