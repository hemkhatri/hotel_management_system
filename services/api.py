from django.db import transaction
from rest_framework import decorators, permissions, response, status, viewsets

from hotels.api import StaffWriteReadOnly
from .models import Order, OrderItem, Service, SubServiceItem
from .serializers import OrderItemSerializer, OrderSerializer, ServiceSerializer, SubServiceItemSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    """Expose the public service menu and allow staff to maintain services."""

    serializer_class = ServiceSerializer
    permission_classes = (StaffWriteReadOnly,)

    def get_queryset(self):
        queryset = Service.objects.select_related("hotel").prefetch_related("items").order_by("name")
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        return queryset


class SubServiceItemViewSet(viewsets.ModelViewSet):
    """Expose service items and allow staff to maintain prices and availability."""

    serializer_class = SubServiceItemSerializer
    permission_classes = (StaffWriteReadOnly,)
    queryset = SubServiceItem.objects.select_related("service", "service__hotel").order_by("name")


class OrderViewSet(viewsets.ModelViewSet):
    """Let authenticated guests order services on their own booking and staff process those orders."""

    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Customers only receive orders tied to their own bookings; staff can process all orders.
        queryset = Order.objects.select_related("booking", "booking__hotel", "booking__customer_id").prefetch_related(
            "items__item__service"
        ).order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(booking__customer_id=self.request.user)

    def update(self, request, *args, **kwargs):
        # Status transitions are staff-controlled; guests use the cancel action below.
        if not request.user.is_staff:
            return response.Response({"detail": "Only staff can update an order."}, status=403)
        return super().update(request, *args, **kwargs)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAdminUser,))
    def set_status(self, request, pk=None):
        """Let staff process an order status; valid choices return the updated order as HTTP 200."""
        order = self.get_object()
        next_status = request.data.get("status")
        allowed = {value for value, _label in Order.OrderStatus.choices}
        if next_status not in allowed:
            return response.Response({"status": [f"Choose one of: {', '.join(sorted(allowed))}."]}, status=400)
        order.status = next_status
        order.save(update_fields=("status", "updated_at"))
        order.update_subtotal()
        return response.Response(self.get_serializer(order).data)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAuthenticated,))
    def cancel(self, request, pk=None):
        """Cancel an unprocessed order; HTTP 200 returns the cancelled order or 400 explains the state."""
        order = self.get_object()
        if not request.user.is_staff and order.status != Order.OrderStatus.PENDING:
            return response.Response({"detail": "Only pending orders can be cancelled."}, status=400)
        if order.status in (Order.OrderStatus.DELIVERED, Order.OrderStatus.CANCELLED):
            return response.Response({"detail": "This order can no longer be cancelled."}, status=400)
        order.status = Order.OrderStatus.CANCELLED
        order.save(update_fields=("status", "updated_at"))
        order.update_subtotal()
        return response.Response(self.get_serializer(order).data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """Allow staff to make order-line adjustments; saves refresh both order and booking totals."""

    serializer_class = OrderItemSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = OrderItem.objects.select_related("order", "order__booking", "item").all()

    @transaction.atomic
    def perform_destroy(self, instance):
        # Recalculate totals after removing a line so the API never leaves stale billing data.
        order = instance.order
        instance.delete()
        order.update_subtotal()
