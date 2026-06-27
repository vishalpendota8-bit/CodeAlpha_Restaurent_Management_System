"""Order domain logic: placement, totals, completion and cancellation.

All state-changing operations run inside atomic transactions so inventory,
order records and table status never drift out of sync.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.inventory import services as inventory_services
from apps.menu.models import MenuItem
from apps.tables.models import RestaurantTable

from .models import Order, OrderItem

CENTS = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def _resolve_items(raw_items: list[dict]) -> list[tuple[MenuItem, int]]:
    """
    Turn ``[{"menu_item": id, "quantity": n}, ...]`` into (MenuItem, qty) pairs.

    Validates that every item exists and is currently available.
    """
    if not raw_items:
        raise ValidationError("An order must contain at least one item.")

    menu_item_ids = [item["menu_item"] for item in raw_items]
    menu_items = MenuItem.objects.in_bulk(menu_item_ids)

    resolved: list[tuple[MenuItem, int]] = []
    for entry in raw_items:
        menu_item = menu_items.get(entry["menu_item"])
        if menu_item is None:
            raise ValidationError(
                f"Menu item {entry['menu_item']} does not exist."
            )
        if not menu_item.available:
            raise ValidationError(f"'{menu_item.name}' is not available.")
        quantity = int(entry["quantity"])
        if quantity < 1:
            raise ValidationError(
                f"Quantity for '{menu_item.name}' must be at least 1."
            )
        resolved.append((menu_item, quantity))
    return resolved


def calculate_totals(items: list[tuple[MenuItem, int]]) -> dict:
    """Compute subtotal, tax and total for resolved (MenuItem, qty) pairs."""
    subtotal = sum((item.price * qty for item, qty in items), Decimal("0"))
    tax = _money(subtotal * Decimal(str(settings.TAX_RATE)))
    subtotal = _money(subtotal)
    total = _money(subtotal + tax)
    return {"subtotal": subtotal, "tax": tax, "total": total}


@transaction.atomic
def place_order(*, table: RestaurantTable, waiter, raw_items: list[dict]) -> Order:
    """
    Create an order end to end:

    1. Validate menu availability.
    2. Check ingredient stock for the whole order.
    3. Persist the order and its line items with captured prices.
    4. Deduct inventory.
    5. Mark the table occupied.
    """
    items = _resolve_items(raw_items)

    # Raises InsufficientStockError if anything is short.
    inventory_services.check_stock(items)

    totals = calculate_totals(items)
    order = Order.objects.create(
        table=table,
        waiter=waiter,
        status=Order.Status.PENDING,
        **totals,
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                price=menu_item.price,
            )
            for menu_item, quantity in items
        ]
    )

    inventory_services.deduct_for_items(items, note=f"order #{order.pk}")

    if table.status != RestaurantTable.Status.OCCUPIED:
        table.status = RestaurantTable.Status.OCCUPIED
        table.save(update_fields=["status"])

    return order


def _order_items_as_pairs(order: Order) -> list[tuple[MenuItem, int]]:
    return [(item.menu_item, item.quantity) for item in order.items.all()]


@transaction.atomic
def complete_order(order: Order) -> Order:
    """Mark an order paid/completed and free its table."""
    if order.status == Order.Status.CANCELLED:
        raise ValidationError("A cancelled order cannot be completed.")
    if order.status == Order.Status.COMPLETED:
        raise ValidationError("Order is already completed.")

    order.status = Order.Status.COMPLETED
    order.payment_status = Order.PaymentStatus.PAID
    order.save(update_fields=["status", "payment_status", "updated_at"])

    table = order.table
    has_open_orders = (
        table.orders.filter(status=Order.Status.PENDING).exclude(pk=order.pk).exists()
    )
    if not has_open_orders:
        table.status = RestaurantTable.Status.AVAILABLE
        table.save(update_fields=["status"])
    return order


@transaction.atomic
def cancel_order(order: Order) -> Order:
    """Cancel a pending order, restore its inventory and free the table."""
    if order.status == Order.Status.COMPLETED:
        raise ValidationError("A completed order cannot be cancelled.")
    if order.status == Order.Status.CANCELLED:
        raise ValidationError("Order is already cancelled.")

    inventory_services.restore_for_items(
        _order_items_as_pairs(order), note=f"cancel order #{order.pk}"
    )

    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])

    table = order.table
    has_open_orders = (
        table.orders.filter(status=Order.Status.PENDING).exclude(pk=order.pk).exists()
    )
    if not has_open_orders:
        table.status = RestaurantTable.Status.AVAILABLE
        table.save(update_fields=["status"])
    return order
