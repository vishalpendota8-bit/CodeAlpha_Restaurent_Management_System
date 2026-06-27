from django.core.validators import MinValueValidator
from django.db import models

from apps.tables.models import RestaurantTable


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SEATED = "SEATED", "Seated"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    table = models.ForeignKey(
        RestaurantTable, related_name="reservations", on_delete=models.CASCADE
    )
    reservation_time = models.DateTimeField()
    guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Reservations are treated as occupying a table for this window.
    SLOT_DURATION_MINUTES = 90

    class Meta:
        ordering = ["reservation_time"]

    def __str__(self) -> str:
        return (
            f"{self.customer_name} — Table {self.table.table_number} "
            f"@ {self.reservation_time:%Y-%m-%d %H:%M}"
        )

    @property
    def is_active(self) -> bool:
        return self.status in {
            self.Status.PENDING,
            self.Status.CONFIRMED,
            self.Status.SEATED,
        }
