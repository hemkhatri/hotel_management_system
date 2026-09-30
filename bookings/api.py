from django.db import transaction
from rest_framework import decorators, permissions, response, status, viewsets

from .models import Booking, BookingRoom
from .serializers import BookingRoomWriteSerializer, BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """Let customers manage their bookings and staff review or transition every booking."""

    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Customers only see their own records; staff sees the full hotel booking ledger.
        queryset = Booking.objects.select_related("customer_id", "hotel").prefetch_related(
            "booking_rooms__room__category__amenities", "orders__items__item"
        ).order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(customer_id=self.request.user)

    def update(self, request, *args, **kwargs):
        # Only staff can edit financial terms or operational fields on an existing booking.
        if not request.user.is_staff:
            return response.Response({"detail": "Only staff can edit a booking."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Preserve financial and audit history; customers cancel through the explicit status action.
        if not request.user.is_staff:
            return response.Response({"detail": "Only staff can delete a booking."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAuthenticated,))
    def cancel(self, request, pk=None):
        """Cancel an eligible booking; HTTP 200 returns the updated booking or 400 explains why not."""
        booking = self.get_object()
        if not request.user.is_staff and booking.status not in (Booking.StatusChoices.PENDING, Booking.StatusChoices.CONFIRMED):
            return response.Response({"detail": "Only pending or confirmed bookings can be cancelled."}, status=400)
        if booking.status in (Booking.StatusChoices.CHECKED_IN, Booking.StatusChoices.CHECKED_OUT):
            return response.Response({"detail": "A checked-in or completed booking cannot be cancelled."}, status=400)
        booking.status = Booking.StatusChoices.CANCELLED
        booking.save(update_fields=("status", "updated_at"))
        return response.Response(self.get_serializer(booking).data)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAdminUser,))
    def set_status(self, request, pk=None):
        """Let staff change operational status; valid choices return the updated booking as HTTP 200."""
        booking = self.get_object()
        next_status = request.data.get("status")
        allowed = {value for value, _label in Booking.StatusChoices.choices}
        if next_status not in allowed:
            return response.Response({"status": [f"Choose one of: {', '.join(sorted(allowed))}."]}, status=400)
        booking.status = next_status
        booking.save(update_fields=("status", "updated_at"))
        return response.Response(self.get_serializer(booking).data)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAdminUser,))
    def check_in(self, request, pk=None):
        """Check in a confirmed guest; HTTP 200 means status and check-in flag were both saved."""
        booking = self.get_object()
        if booking.status != Booking.StatusChoices.CONFIRMED:
            return response.Response({"detail": "Only confirmed bookings can be checked in."}, status=400)
        booking.status = Booking.StatusChoices.CHECKED_IN
        booking.check_in_status = True
        booking.save(update_fields=("status", "check_in_status", "updated_at"))
        return response.Response(self.get_serializer(booking).data)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAdminUser,))
    def check_out(self, request, pk=None):
        """Check out an in-house guest; HTTP 200 means status and check-out flag were both saved."""
        booking = self.get_object()
        if booking.status != Booking.StatusChoices.CHECKED_IN:
            return response.Response({"detail": "Only checked-in bookings can be checked out."}, status=400)
        booking.status = Booking.StatusChoices.CHECKED_OUT
        booking.check_out_status = True
        booking.save(update_fields=("status", "check_out_status", "updated_at"))
        return response.Response(self.get_serializer(booking).data)


class BookingRoomViewSet(viewsets.ModelViewSet):
    """Allow staff to adjust booking room lines while preserving price snapshots and totals."""

    serializer_class = BookingRoomWriteSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = BookingRoom.objects.select_related("booking", "room").all()

    @transaction.atomic
    def perform_destroy(self, instance):
        # Delete the line and refresh totals so the successful 204 response leaves consistent billing.
        booking = instance.booking
        instance.delete()
        booking.update_totals()
