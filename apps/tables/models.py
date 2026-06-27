from django.core.validators import MinValueValidator
from django.db import models


class RestaurantTable(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        OCCUPIED = "OCCUPIED", "Occupied"

    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["table_number"]

    def __str__(self) -> str:
        return f"Table {self.table_number} ({self.get_status_display()})"

    @property
    def is_available(self) -> bool:
        return self.status == self.Status.AVAILABLE
