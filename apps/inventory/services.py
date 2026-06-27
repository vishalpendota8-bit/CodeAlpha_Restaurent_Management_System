"""Inventory domain logic: stock checks, deduction, restoration, logging."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from .models import Ingredient, InventoryLog, Recipe


class InsufficientStockError(Exception):
    """Raised when an ingredient does not have enough stock for an order."""

    def __init__(self, shortages: list[dict]):
        self.shortages = shortages
        message = "; ".join(
            f"{s['ingredient']}: need {s['required']} {s['unit']}, have {s['available']}"
            for s in shortages
        )
        super().__init__(f"Insufficient stock — {message}")


def required_ingredients(menu_item, quantity) -> list[tuple[Recipe, Decimal]]:
    """Return (recipe, total_amount) pairs for ``quantity`` of a menu item."""
    quantity = Decimal(quantity)
    return [
        (recipe, recipe.quantity_required * quantity)
        for recipe in menu_item.recipes.select_related("ingredient")
    ]


def check_stock(items: list[tuple]) -> None:
    """
    Validate that every ingredient required by ``items`` is in stock.

    ``items`` is a list of (menu_item, quantity) tuples.
    Raises ``InsufficientStockError`` listing all shortages if any are found.
    """
    needed: dict[int, Decimal] = {}
    ref: dict[int, Ingredient] = {}
    for menu_item, quantity in items:
        for recipe, amount in required_ingredients(menu_item, quantity):
            needed[recipe.ingredient_id] = (
                needed.get(recipe.ingredient_id, Decimal("0")) + amount
            )
            ref[recipe.ingredient_id] = recipe.ingredient

    shortages = []
    for ingredient_id, amount in needed.items():
        ingredient = ref[ingredient_id]
        if ingredient.quantity < amount:
            shortages.append(
                {
                    "ingredient": ingredient.name,
                    "required": amount,
                    "available": ingredient.quantity,
                    "unit": ingredient.unit,
                }
            )
    if shortages:
        raise InsufficientStockError(shortages)


@transaction.atomic
def deduct_for_items(items: list[tuple], note: str = "") -> None:
    """Deduct ingredient stock for the given (menu_item, quantity) items."""
    needed: dict[int, Decimal] = {}
    for menu_item, quantity in items:
        for recipe, amount in required_ingredients(menu_item, quantity):
            needed[recipe.ingredient_id] = (
                needed.get(recipe.ingredient_id, Decimal("0")) + amount
            )

    for ingredient_id, amount in needed.items():
        Ingredient.objects.filter(pk=ingredient_id).update(
            quantity=F("quantity") - amount
        )
        InventoryLog.objects.create(
            ingredient_id=ingredient_id,
            quantity=amount,
            action=InventoryLog.Action.DEDUCT,
            note=note,
        )


@transaction.atomic
def restore_for_items(items: list[tuple], note: str = "") -> None:
    """Return ingredient stock for cancelled (menu_item, quantity) items."""
    needed: dict[int, Decimal] = {}
    for menu_item, quantity in items:
        for recipe, amount in required_ingredients(menu_item, quantity):
            needed[recipe.ingredient_id] = (
                needed.get(recipe.ingredient_id, Decimal("0")) + amount
            )

    for ingredient_id, amount in needed.items():
        Ingredient.objects.filter(pk=ingredient_id).update(
            quantity=F("quantity") + amount
        )
        InventoryLog.objects.create(
            ingredient_id=ingredient_id,
            quantity=amount,
            action=InventoryLog.Action.RESTORE,
            note=note,
        )


@transaction.atomic
def restock(ingredient: Ingredient, amount: Decimal, note: str = "") -> Ingredient:
    """Increase an ingredient's stock and log the restock."""
    amount = Decimal(amount)
    Ingredient.objects.filter(pk=ingredient.pk).update(
        quantity=F("quantity") + amount
    )
    InventoryLog.objects.create(
        ingredient=ingredient,
        quantity=amount,
        action=InventoryLog.Action.RESTOCK,
        note=note,
    )
    ingredient.refresh_from_db()
    return ingredient


def low_stock_ingredients():
    """Queryset of ingredients at or below their minimum stock level."""
    return Ingredient.objects.filter(quantity__lte=F("minimum_stock"))
