from django.db import transaction
from rest_framework import serializers

from .models import Order, OrderItem, Service, SubServiceItem


class SubServiceItemSerializer(serializers.ModelSerializer):
    """Expose service item price and availability; the server owns these catalog values."""

    class Meta:
        model = SubServiceItem
        fields = ("id", "service", "name", "description", "price", "is_available", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_price(self, value):
        # Reject negative catalog prices; successful output will always contain a non-negative price.
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value


class ServiceSerializer(serializers.ModelSerializer):
    """Return a service with its available items so frontends can build service menus."""

    items = SubServiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = ("id", "hotel", "name", "description", "category", "custom_category_name", "items", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        # The model requires a custom label for OTHER; return a field error instead of saving bad catalog data.
        category = attrs.get("category", getattr(self.instance, "category", Service.CategoryChoices.ROOM_SERVICE))
        custom_name = attrs.get("custom_category_name", getattr(self.instance, "custom_category_name", None))
        if category == Service.CategoryChoices.OTHER and not custom_name:
            raise serializers.ValidationError({"custom_category_name": "Required when category is OTHER."})
        return attrs


class OrderItemReadSerializer(serializers.ModelSerializer):
    """Return order line snapshots, including the selected service item name."""

    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "item", "item_name", "quantity", "unit_price", "subtotal", "created_at")


class OrderLineInputSerializer(serializers.Serializer):
    """Validate a requested menu item and quantity before the order is written."""

    item = serializers.PrimaryKeyRelatedField(queryset=SubServiceItem.objects.select_related("service"))
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class OrderSerializer(serializers.ModelSerializer):
    """Create a service order from item IDs and return server-calculated line and order totals."""

    items = OrderItemReadSerializer(many=True, read_only=True)
    lines = OrderLineInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Order
        fields = ("id", "booking", "status", "subtotal", "items", "lines", "created_at", "updated_at")
        read_only_fields = ("id", "status", "subtotal", "created_at", "updated_at")

    def validate(self, attrs):
        # Ensure the customer owns the booking and that each item belongs to the same hotel's menu.
        booking = attrs.get("booking")
        request = self.context.get("request")
        if booking and request and not request.user.is_staff and booking.customer_id_id != request.user.pk:
            raise serializers.ValidationError({"booking": "You can only order for your own booking."})
        if booking and booking.status in ("CANCELLED", "EXPIRED", "CHECKED_OUT"):
            raise serializers.ValidationError({"booking": "This booking cannot accept service orders."})
        lines = attrs.get("lines", [])
        if not lines and self.instance is None:
            raise serializers.ValidationError({"lines": "Add at least one service item."})
        selected = {line["item"].pk: line["item"] for line in lines}
        for index, line in enumerate(lines):
            item = selected.get(line["item"].pk)
            if booking and item.service.hotel_id != booking.hotel_id:
                raise serializers.ValidationError({"lines": {index: "Selected item does not belong to the booking hotel."}})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Each OrderItem snapshots its current price; any invalid item rolls back the entire order.
        lines = validated_data.pop("lines")
        order = Order.objects.create(**validated_data)
        for line in lines:
            OrderItem.objects.create(order=order, **line)
        order.update_subtotal()
        return order

    def update(self, instance, validated_data):
        # Order line edits are handled by staff through the dedicated order-item endpoint.
        validated_data.pop("lines", None)
        return super().update(instance, validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    """Create or update a line using the catalog's current price and model validations."""

    class Meta:
        model = OrderItem
        fields = ("id", "order", "item", "quantity", "unit_price", "subtotal", "created_at")
        read_only_fields = ("id", "unit_price", "subtotal", "created_at")

    def update(self, instance, validated_data):
        # Changing the selected item snapshots that item's current price before model totals recalculate.
        new_item = validated_data.get("item")
        if new_item and new_item.pk != instance.item_id:
            instance.unit_price = new_item.price
        return super().update(instance, validated_data)
