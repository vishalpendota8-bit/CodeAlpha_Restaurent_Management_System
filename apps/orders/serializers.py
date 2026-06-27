from rest_framework import serializers

from apps.menu.models import MenuItem

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    line_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "quantity",
            "price",
            "line_total",
        ]
        read_only_fields = ["id", "price", "line_total"]


class OrderItemInputSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    """Read serializer returning the full order with its line items."""

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )
    table_number = serializers.IntegerField(
        source="table.table_number", read_only=True
    )
    waiter_username = serializers.CharField(
        source="waiter.username", read_only=True, default=None
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "table",
            "table_number",
            "waiter",
            "waiter_username",
            "status",
            "status_display",
            "payment_status",
            "payment_status_display",
            "subtotal",
            "tax",
            "total",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    """Write serializer for placing a new order."""

    table = serializers.PrimaryKeyRelatedField(
        queryset=Order._meta.get_field("table").related_model.objects.all()
    )
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Provide at least one item to place an order."
            )
        return value

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data
