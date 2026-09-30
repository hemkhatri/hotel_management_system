from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Sum


class Booking(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    class BookingSourceChoices(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        OFFLINE = 'OFFLINE', 'Offline'

    user = models.ForeignKey(
        'accounts.UserModel',
        on_delete=models.PROTECT,
        related_name='bookings',
    )
    hotel = models.ForeignKey('hotels.Hotel', on_delete=models.CASCADE)
    number_of_guests = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Total number of guests for this booking',
    )
    check_in = models.DateField()
    check_in_status = models.BooleanField(default=False)

    check_out = models.DateField(null=True, blank=True)
    check_out_status = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    booking_source = models.CharField(
        max_length=10,
        choices=BookingSourceChoices.choices,
        default=BookingSourceChoices.ONLINE,
    )
    special_request = models.TextField(blank=True, default='')

    order_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal('0.00'),
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal('0.00'),
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_subtotals(self, save=True):
        room_subtotal = self.booking_rooms.aggregate(
            total=Sum('subtotal_room')
        )['total'] or Decimal('0.00')
        self.subtotal = room_subtotal

        if hasattr(self, 'orders'):
            self.order_total = self.orders.aggregate(
                total=Sum('subtotal')
            )['total'] or Decimal('0.00')

        self.discount = (
            self.subtotal * (self.discount_percentage / Decimal('100'))
        ).quantize(Decimal('0.01'))

        taxable_amount = (self.subtotal - self.discount) + self.order_total

        self.tax = (
            taxable_amount * (self.tax_percentage / Decimal('100'))
        ).quantize(Decimal('0.01'))

        self.total = taxable_amount + self.tax

        if save:
            self.save(update_fields=['subtotal', 'order_total', 'discount', 'tax', 'total', 'updated_at'])

    def clean(self):
        super().clean()

        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise ValidationError({
                'check_out': 'The check-out date must be after the check-in date.'
            })

        if self.check_in_status and not self.check_in:
            raise ValidationError({
                'check_in': 'The check-in status is active, but the check-in date is missing.'
            })

        if self.check_out_status and not self.check_out:
            raise ValidationError({
                'check_out': 'The check-out status is active, but the check-out date is missing.'
            })


class BookingRoom(models.Model):
    booking = models.ForeignKey(
        'Booking', on_delete=models.CASCADE, related_name='booking_rooms'
    )
    room = models.ForeignKey(
        'rooms.Room', on_delete=models.PROTECT, related_name='room_bookings'
    )
    booked_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    number_of_nights = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(365)]
    )
    subtotal_room = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
    )
    is_available = models.BooleanField(default=True)
    available_date = models.DateField(blank=True, null=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def price_per_night(self):
        if self.booked_price is not None:
            return self.booked_price
        if self.room and hasattr(self.room, 'category') and self.room.category:
            return self.room.category.base_price
        return Decimal('0.00')

    @property
    def calculated_available_date(self):
        if self.booking and self.booking.check_in:
            return self.booking.check_in + timedelta(days=self.number_of_nights)
        return None

    def clean(self):
        super().clean()
        if self.room and self.booking and self.booking.check_in and self.booking.check_out:
            active_statuses = [
                Booking.StatusChoices.PENDING,
                Booking.StatusChoices.CONFIRMED,
                Booking.StatusChoices.CHECKED_IN,
            ]
            overlapping_bookings = BookingRoom.objects.filter(
                room=self.room,
                booking__status__in=active_statuses,
                booking__check_in__lt=self.booking.check_out,
                booking__check_out__gt=self.booking.check_in
            ).exclude(pk=self.pk)

            if overlapping_bookings.exists():
                raise ValidationError(f"Room {self.room.room_number} is already reserved for these dates.")

    def save(self, *args, **kwargs):
        if self.booked_price is None and self.room and hasattr(self.room, 'category'):
            self.booked_price = self.room.category.base_price

        self.subtotal_room = (
            self.price_per_night * self.number_of_nights
        ).quantize(Decimal('0.01'))

        if self.booking and self.booking.check_in:
            self.available_date = self.calculated_available_date

        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.booking_id:
                self.booking.update_subtotals(save=True)

    def __str__(self):
        return f'Room {self.room.room_number} booked for booking #{self.booking.id}'