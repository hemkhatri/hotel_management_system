from django.utils.dateparse import parse_datetime
from rest_framework import viewsets

from bookings.models import Booking, BookingRoom
from hotels.api import StaffWriteReadOnly
from .models import Room, RoomMedia
from .serializers import RoomMediaSerializer, RoomSerializer


class RoomViewSet(viewsets.ModelViewSet):
    """List room inventory and filter availability by date; staff manage room records."""

    serializer_class = RoomSerializer
    permission_classes = (StaffWriteReadOnly,)

    def get_queryset(self):
        queryset = Room.objects.select_related("category").prefetch_related("category__amenities", "roommedia_set").order_by("room_number")
        check_in = self.request.query_params.get("check_in")
        check_out = self.request.query_params.get("check_out")
        if check_in and check_out:
            start, end = parse_datetime(check_in), parse_datetime(check_out)
            if start and end and end > start:
                conflicts = BookingRoom.objects.filter(
                    room_id__in=queryset.values("id"),
                    booking__check_in__lt=end,
                    booking__check_out__gt=start,
                ).exclude(booking__status__in=(Booking.StatusChoices.CANCELLED, Booking.StatusChoices.EXPIRED)).values("room_id")
                queryset = queryset.exclude(id__in=conflicts)
            else:
                queryset = queryset.none()
        if self.request.query_params.get("available", "").lower() == "true":
            queryset = queryset.filter(status=Room.RoomStatusChoices.AVAILABLE)
        return queryset


class RoomMediaViewSet(viewsets.ModelViewSet):
    """Manage room image/video metadata; this model stores captions and type but no uploaded file."""

    queryset = RoomMedia.objects.select_related("room").all()
    serializer_class = RoomMediaSerializer
    permission_classes = (StaffWriteReadOnly,)
