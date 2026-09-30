from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from hotels.serializers import HotelSerializer
from rooms.models import Room
from rooms.serializers import RoomSerializer
from .models import Booking, BookingRoom


class BookingRoomSerializer(serializers.ModelSerializer):
    """Return the room and price snapshot attached to a booking."""

    room_detail = RoomSerializer(source="room", read_only=True)

    class Meta:
        model = BookingRoom
        fields = ("id", "room", "room_detail", "price_per_night", "number_of_nights", "subtotal", "created_at")
        read_only_fields = ("id", "price_per_night", "subtotal", "created_at")


class BookingSerializer(serializers.ModelSerializer):
    """Create bookings from selected room IDs and return totals, room details, and booking status."""

    customer = serializers.SerializerMethodField()
    hotel_detail = HotelSerializer(source="hotel", read_only=True)
    rooms = BookingRoomSerializer(source="booking_rooms", many=True, read_only=True)
    room_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Room.objects.select_related("category").all(),
        write_only=True, required=False,
    )
    number_of_guests = serializers.IntegerField(min_value=1)

    class Meta:
        model = Booking
        fields = (
            "id", "customer_id", "customer", "hotel", "hotel_detail", "check_in", "check_out",
            "check_in_status", "check_out_status", "number_of_guests", "status", "booking_source", "special_requests", "rooms",
            "room_ids", "subtotal", "discount", "tax", "total", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "customer_id", "customer", "status", "booking_source", "check_in_status",
            "check_out_status", "subtotal", "total",
            "created_at", "updated_at",
        )

    def get_customer(self, obj):
        # Customer contact fields are available to staff and to the booking's own customer only.
        request = self.context.get("request")
        if request and (request.user.is_staff or request.user.pk == obj.customer_id_id):
            return {"id": obj.customer_id_id, "username": obj.customer_id.username, "email": obj.customer_id.email}
        return None

    def validate(self, attrs):
        # The API refuses invalid dates, past check-ins, over-capacity room choices, and conflicts.
        start = attrs.get("check_in", getattr(self.instance, "check_in", None))
        end = attrs.get("check_out", getattr(self.instance, "check_out", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"check_out": "Check-out must be after check-in."})
        if start and start < timezone.now() and self.instance is None:
            raise serializers.ValidationError({"check_in": "Check-in cannot be in the past."})

        room_ids = attrs.get("room_ids")
        if room_ids is not None or self.instance is None:
            rooms = list(room_ids or [])
            if not rooms:
                raise serializers.ValidationError({"room_ids": "Select at least one room."})
            if len({room.pk for room in rooms}) != len(rooms):
                raise serializers.ValidationError({"room_ids": "A room can only be selected once."})
            guests = attrs.get("number_of_guests", getattr(self.instance, "number_of_guests", 0))
            if sum(room.category.max_occupancy for room in rooms) < guests:
                raise serializers.ValidationError({"number_of_guests": "Selected rooms do not have enough guest capacity."})
            if start and end and end > start:
                conflicts = BookingRoom.objects.filter(
                    room__in=rooms, booking__check_in__lt=end, booking__check_out__gt=start
                ).exclude(booking__status__in=(Booking.StatusChoices.CANCELLED, Booking.StatusChoices.EXPIRED))
                if self.instance:
                    conflicts = conflicts.exclude(booking=self.instance)
                if conflicts.exists():
                    raise serializers.ValidationError({"room_ids": "One or more rooms are already booked for these dates."})
                unavailable = [room.room_number for room in rooms if room.status != Room.RoomStatusChoices.AVAILABLE]
                if unavailable:
                    raise serializers.ValidationError({"room_ids": f"Rooms are not available: {', '.join(unavailable)}."})
        return attrs

    def get_fields(self):
        # Guests can never set discounts or tax; staff may enter those values for approved adjustments.
        fields = super().get_fields()
        request = self.context.get("request")
        if not request or not request.user.is_staff:
            fields["discount"].read_only = True
            fields["tax"].read_only = True
        return fields

    @transaction.atomic
    def create(self, validated_data):
        # Create the booking and price-snapshot room rows as one transaction; 201 means all succeeded.
        rooms = validated_data.pop("room_ids")
        booking = Booking.objects.create(
            customer_id=self.context["request"].user,
            booking_source=Booking.BookingSourceChoices.ONLINE,
            **validated_data,
        )
        nights = max(1, (booking.check_out.date() - booking.check_in.date()).days)
        for room in rooms:
            BookingRoom.objects.create(booking=booking, room=room, number_of_nights=nights)
        booking.update_totals()
        return booking

    @transaction.atomic
    def update(self, instance, validated_data):
        # Staff room replacements are atomic, and every line is repriced from its room category.
        rooms = validated_data.pop("room_ids", None)
        booking = super().update(instance, validated_data)
        if rooms is not None:
            booking.booking_rooms.all().delete()
            nights = max(1, (booking.check_out.date() - booking.check_in.date()).days)
            for room in rooms:
                BookingRoom.objects.create(booking=booking, room=room, number_of_nights=nights)
        booking.update_totals()
        return booking


class BookingRoomWriteSerializer(serializers.ModelSerializer):
    """Accept a room and night count for staff booking adjustments; price totals are server-owned."""

    number_of_nights = serializers.IntegerField(min_value=1)

    class Meta:
        model = BookingRoom
        fields = ("id", "booking", "room", "number_of_nights", "price_per_night", "subtotal", "created_at")
        read_only_fields = ("id", "price_per_night", "subtotal", "created_at")

    def validate(self, attrs):
        # Prevent an adjustment from attaching a room that is occupied by another active booking.
        booking = attrs.get("booking", getattr(self.instance, "booking", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        if booking and room and BookingRoom.objects.filter(
            room=room, booking__check_in__lt=booking.check_out, booking__check_out__gt=booking.check_in
        ).exclude(booking__status__in=(Booking.StatusChoices.CANCELLED, Booking.StatusChoices.EXPIRED)).exclude(
            booking=booking
        ).exists():
            raise serializers.ValidationError({"room": "This room is unavailable for the booking dates."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Saving the related booking room automatically refreshes the parent booking total.
        return BookingRoom.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        # Save recalculates this room line and its booking total using the model's pricing rules.
        return super().update(instance, validated_data)
