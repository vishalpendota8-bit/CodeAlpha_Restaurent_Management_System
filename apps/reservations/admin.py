from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "table",
        "reservation_time",
        "guests",
        "status",
    )
    list_filter = ("status", "reservation_time")
    search_fields = ("customer_name", "phone")
    date_hierarchy = "reservation_time"
