from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import RolePermission
from apps.accounts.models import User
from apps.inventory.services import InsufficientStockError

from . import services
from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders API.

    - ``POST /orders`` places an order (validates stock, deducts inventory).
    - ``POST /orders/{id}/complete`` settles payment and frees the table.
    - ``POST /orders/{id}/cancel`` restores inventory and frees the table.

    Updating/deleting orders directly is intentionally disabled; use the
    domain actions so inventory and table state stay consistent.
    """

    queryset = (
        Order.objects.select_related("table", "waiter")
        .prefetch_related("items__menu_item")
        .all()
    )
    permission_classes = [RolePermission]
    allowed_roles = [User.Role.ADMIN, User.Role.MANAGER, User.Role.WAITER]
    filterset_fields = ["status", "payment_status", "table", "waiter"]
    ordering_fields = ["created_at", "total"]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        raw_items = [
            {"menu_item": item["menu_item"].id, "quantity": item["quantity"]}
            for item in data["items"]
        ]
        try:
            order = services.place_order(
                table=data["table"],
                waiter=request.user,
                raw_items=raw_items,
            )
        except InsufficientStockError as exc:
            return Response(
                {"detail": str(exc), "shortages": exc.shortages},
                status=status.HTTP_409_CONFLICT,
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        output = OrderSerializer(order, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()
        try:
            order = services.complete_order(order)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order = services.cancel_order(order)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(OrderSerializer(order).data)
