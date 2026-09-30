from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from bookings.models import Booking, BookingRoom

class Room(models.Model):
    class RoomStatusChoices(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        RESERVED = 'RESERVED', 'Reserved'

    hotel = models.ForeignKey(
        'hotels.Hotel', 
        on_delete=models.CASCADE,
        related_name='rooms'    
    )
    category = models.ForeignKey(
        'hotels.RoomCategory',
        on_delete=models.PROTECT
    )
    room_number = models.CharField(max_length=20)
    floor = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=RoomStatusChoices.choices,
        default=RoomStatusChoices.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['hotel', 'room_number'], name='unique_room_per_hotel')
        ]

    @classmethod
    def get_available_rooms(cls, hotel, check_in_date, check_out_date):
        active_statuses = [
            Booking.StatusChoices.PENDING,
            Booking.StatusChoices.CONFIRMED,
            Booking.StatusChoices.CHECKED_IN,
        ]

        booked_room_ids = BookingRoom.objects.filter(
            booking__hotel = hotel,
            booking__status__in=active_statuses,
            booking__check_in__lt=check_out_date,
            booking__check_out__gt=check_in_date,
        ).values_list('room_id', flat=True)

        return cls.objects.filter(
            hotel = hotel, 
            status = cls.RoomStatusChoices.AVAILABLE,
        ).exclude(
            id__in = booked_room_ids
        )

    def clean(self):
        super().clean()
        if self.hotel and hasattr(self.hotel, 'no_of_floor'):
            if self.floor > self.hotel.no_of_floor:
                raise ValidationError({
                    'floor': f"This hotel only has {self.hotel.no_of_floor} floors. You can't assign this room on floor {self.floor}."
                })

    def __str__(self):
        return f"{self.room_number} ({self.hotel})"


class RoomMedia(models.Model):
    class MediaChoices(models.TextChoices):
        IMAGE = 'IMG', 'Image'
        VIDEO = 'VDO', 'Video'
        GIF = 'GIF', 'GIF'

    room = models.ForeignKey(
        'Room', 
        on_delete=models.CASCADE,
        related_name='media'
    )
    media_type = models.CharField(
        max_length=3, 
        choices=MediaChoices.choices, 
        default=MediaChoices.IMAGE
    )
    caption = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-media_type', '-created_at']

    def __str__(self):
        return f"{self.get_media_type_display()} for Room {self.room.room_number}"