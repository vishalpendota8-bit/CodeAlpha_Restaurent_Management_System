"""Reservation domain logic: availability, capacity and double-booking checks."""
from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.tables.models import RestaurantTable

from .models import Reservation

ACTIVE_STATUSES = [
    Reservation.Status.PENDING,
    Reservation.Status.CONFIRMED,
    Reservation.Status.SEATED,
]


def overlapping_reservations(table, reservation_time, exclude_pk=None):
    """Return active reservations for ``table`` whose slot overlaps the request."""
    duration = timedelta(minutes=Reservation.SLOT_DURATION_MINUTES)
    start = reservation_time - duration
    end = reservation_time + duration
    qs = Reservation.objects.filter(
        table=table,
        status__in=ACTIVE_STATUSES,
        reservation_time__gt=start,
        reservation_time__lt=end,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs


def validate_reservation(table, reservation_time, guests, exclude_pk=None) -> None:
    """
    Run all reservation business rules.

    Raises ``django.core.exceptions.ValidationError`` on the first failure.
    """
    if guests > table.capacity:
        raise ValidationError(
            f"Table {table.table_number} seats {table.capacity}; "
            f"requested {guests} guests."
        )

    if overlapping_reservations(table, reservation_time, exclude_pk).exists():
        raise ValidationError(
            f"Table {table.table_number} is already booked around "
            f"{reservation_time:%Y-%m-%d %H:%M}."
        )


def available_tables(reservation_time, guests):
    """Tables that can seat ``guests`` and have no conflicting reservation."""
    duration = timedelta(minutes=Reservation.SLOT_DURATION_MINUTES)
    start = reservation_time - duration
    end = reservation_time + duration
    busy_table_ids = (
        Reservation.objects.filter(
            status__in=ACTIVE_STATUSES,
            reservation_time__gt=start,
            reservation_time__lt=end,
        )
        .values_list("table_id", flat=True)
        .distinct()
    )
    return RestaurantTable.objects.filter(
        Q(capacity__gte=guests) & ~Q(id__in=busy_table_ids)
    )


def mark_table_reserved(reservation: Reservation) -> None:
    """Reflect an active reservation on the table's status."""
    table = reservation.table
    if reservation.is_active and table.status == RestaurantTable.Status.AVAILABLE:
        table.status = RestaurantTable.Status.RESERVED
        table.save(update_fields=["status"])


def release_table(reservation: Reservation) -> None:
    """Free a table when its reservation is cancelled/completed and nothing else holds it."""
    table = reservation.table
    still_active = overlapping_reservations(
        table, reservation.reservation_time, exclude_pk=reservation.pk
    ).exists()
    if not still_active and table.status == RestaurantTable.Status.RESERVED:
        table.status = RestaurantTable.Status.AVAILABLE
        table.save(update_fields=["status"])
