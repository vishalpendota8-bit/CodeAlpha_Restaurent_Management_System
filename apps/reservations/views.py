from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import RolePermission
from apps.accounts.models import User
from apps.tables.serializers import RestaurantTableSerializer

from . import services
from .models import Reservation
from .serializers import ReservationSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related("table").all()
    serializer_class = ReservationSerializer
    permission_classes = [RolePermission]
    allowed_roles = [User.Role.ADMIN, User.Role.MANAGER, User.Role.WAITER]
    filterset_fields = ["status", "table", "guests"]
    search_fields = ["customer_name", "phone"]
    ordering_fields = ["reservation_time", "created_at"]

    def perform_create(self, serializer):
        reservation = serializer.save()
        services.mark_table_reserved(reservation)

    def perform_update(self, serializer):
        reservation = serializer.save()
        if reservation.is_active:
            services.mark_table_reserved(reservation)
        else:
            services.release_table(reservation)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """POST /reservations/{id}/cancel — cancel and free the table."""
        reservation = self.get_object()
        if reservation.status == Reservation.Status.CANCELLED:
            return Response(
                {"detail": "Reservation is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        services.release_table(reservation)
        return Response(self.get_serializer(reservation).data)

    @action(detail=False, methods=["get"], url_path="available-tables")
    def available_tables(self, request):
        """GET /reservations/available-tables?time=ISO&guests=N."""
        raw_time = request.query_params.get("time")
        guests = request.query_params.get("guests", "1")
        reservation_time = parse_datetime(raw_time) if raw_time else None
        if reservation_time is None:
            return Response(
                {"detail": "Provide a valid ISO 'time' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            guests = int(guests)
        except ValueError:
            guests = 1
        tables = services.available_tables(reservation_time, guests)
        return Response(RestaurantTableSerializer(tables, many=True).data)
