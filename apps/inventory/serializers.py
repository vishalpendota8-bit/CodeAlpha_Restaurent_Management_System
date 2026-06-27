from decimal import Decimal

from rest_framework import serializers

from .models import Ingredient, InventoryLog, Recipe


class IngredientSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "quantity",
            "unit",
            "minimum_stock",
            "is_low_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecipeSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "ingredient",
            "ingredient_name",
            "quantity_required",
        ]
        read_only_fields = ["id"]

    def validate_quantity_required(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Required quantity must be greater than zero."
            )
        return value


class InventoryLogSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    action_display = serializers.CharField(
        source="get_action_display", read_only=True
    )

    class Meta:
        model = InventoryLog
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "quantity",
            "action",
            "action_display",
            "note",
            "timestamp",
        ]
        read_only_fields = fields


class RestockSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0")
    )
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Restock amount must be positive.")
        return value
