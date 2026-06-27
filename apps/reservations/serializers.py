from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from . import services
from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    table_number = serializers.IntegerField(
        source="table.table_number", read_only=True
    )

    class Meta:
        model = Reservation
        fields = [
            "id",
            "customer_name",
            "phone",
            "table",
            "table_number",
            "reservation_time",
            "guests",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        # Merge incoming data with the existing instance for partial updates.
        table = attrs.get("table") or getattr(self.instance, "table", None)
        reservation_time = attrs.get("reservation_time") or getattr(
            self.instance, "reservation_time", None
        )
        guests = attrs.get("guests") or getattr(self.instance, "guests", None)
        exclude_pk = self.instance.pk if self.instance else None

        try:
            services.validate_reservation(
                table, reservation_time, guests, exclude_pk=exclude_pk
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": exc.messages})
        return attrs
