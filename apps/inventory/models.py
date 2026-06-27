from django.core.validators import MinValueValidator
from django.db import models

from apps.menu.models import MenuItem


class Ingredient(models.Model):
    name = models.CharField(max_length=150, unique=True)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    unit = models.CharField(max_length=30, help_text="e.g. kg, g, l, ml, pcs")
    minimum_stock = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.quantity} {self.unit})"

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.minimum_stock


class Recipe(models.Model):
    """Maps a menu item to the ingredients (and amounts) it consumes."""

    menu_item = models.ForeignKey(
        MenuItem, related_name="recipes", on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, related_name="recipes", on_delete=models.CASCADE
    )
    quantity_required = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ("menu_item", "ingredient")
        ordering = ["menu_item__name"]

    def __str__(self) -> str:
        return (
            f"{self.menu_item.name} needs "
            f"{self.quantity_required} {self.ingredient.unit} of {self.ingredient.name}"
        )


class InventoryLog(models.Model):
    class Action(models.TextChoices):
        RESTOCK = "RESTOCK", "Restock"
        DEDUCT = "DEDUCT", "Deduct"
        RESTORE = "RESTORE", "Restore"
        ADJUST = "ADJUST", "Adjust"

    ingredient = models.ForeignKey(
        Ingredient, related_name="logs", on_delete=models.CASCADE
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    action = models.CharField(max_length=20, choices=Action.choices)
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.get_action_display()} {self.quantity} of {self.ingredient.name}"
