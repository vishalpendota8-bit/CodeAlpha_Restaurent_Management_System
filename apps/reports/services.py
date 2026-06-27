"""Aggregation logic for sales and stock reports."""
from __future__ import annotations

from datetime import date, datetime, time

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.inventory.services import low_stock_ingredients
from apps.orders.models import Order, OrderItem

ZERO = Coalesce(
    Sum("total"), 0, output_field=DecimalField(max_digits=12, decimal_places=2)
)


def _completed_orders():
    return Order.objects.filter(status=Order.Status.COMPLETED)


def daily_sales(report_date: date | None = None) -> dict:
    """Total completed sales and order count for a single day."""
    report_date = report_date or timezone.localdate()
    start = timezone.make_aware(datetime.combine(report_date, time.min))
    end = timezone.make_aware(datetime.combine(report_date, time.max))
    qs = _completed_orders().filter(created_at__range=(start, end))
    aggregate = qs.aggregate(revenue=ZERO)
    return {
        "date": report_date.isoformat(),
        "orders": qs.count(),
        "revenue": aggregate["revenue"],
    }


def monthly_sales(year: int, month: int) -> dict:
    """Total completed sales and a per-day breakdown for a month."""
    qs = _completed_orders().filter(
        created_at__year=year, created_at__month=month
    )
    breakdown = (
        qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total"), orders=Count("id"))
        .order_by("day")
    )
    aggregate = qs.aggregate(revenue=ZERO)
    return {
        "year": year,
        "month": month,
        "orders": qs.count(),
        "revenue": aggregate["revenue"],
        "daily_breakdown": [
            {
                "date": row["day"].isoformat(),
                "revenue": row["revenue"],
                "orders": row["orders"],
            }
            for row in breakdown
        ],
    }


def top_selling_items(limit: int = 10) -> list[dict]:
    """Best-selling menu items by quantity sold across completed orders."""
    rows = (
        OrderItem.objects.filter(order__status=Order.Status.COMPLETED)
        .values("menu_item__id", "menu_item__name")
        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum(F("price") * F("quantity")),
        )
        .order_by("-quantity_sold")[:limit]
    )
    return [
        {
            "menu_item_id": row["menu_item__id"],
            "name": row["menu_item__name"],
            "quantity_sold": row["quantity_sold"],
            "revenue": row["revenue"],
        }
        for row in rows
    ]


def low_stock_report() -> list[dict]:
    """Ingredients at or below their minimum stock level."""
    return [
        {
            "ingredient_id": ingredient.id,
            "name": ingredient.name,
            "quantity": ingredient.quantity,
            "unit": ingredient.unit,
            "minimum_stock": ingredient.minimum_stock,
        }
        for ingredient in low_stock_ingredients()
    ]
