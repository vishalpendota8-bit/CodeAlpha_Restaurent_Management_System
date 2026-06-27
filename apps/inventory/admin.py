from django.contrib import admin

from .models import Ingredient, InventoryLog, Recipe


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "unit", "minimum_stock", "is_low_stock")
    search_fields = ("name",)
    list_editable = ("quantity", "minimum_stock")

    @admin.display(boolean=True, description="Low stock")
    def is_low_stock(self, obj):
        return obj.is_low_stock


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "ingredient", "quantity_required")
    list_filter = ("menu_item", "ingredient")
    search_fields = ("menu_item__name", "ingredient__name")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "action", "quantity", "timestamp")
    list_filter = ("action", "ingredient")
    search_fields = ("ingredient__name", "note")
    readonly_fields = ("ingredient", "quantity", "action", "note", "timestamp")
