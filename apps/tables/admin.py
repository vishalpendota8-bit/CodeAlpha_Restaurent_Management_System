from django.contrib import admin

from .models import RestaurantTable


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "capacity", "status")
    list_filter = ("status",)
    search_fields = ("table_number",)
    list_editable = ("status",)
