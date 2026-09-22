from django.db import models

# Create your models here.
class Booking(models.Model):
    class BookingSourceChoices(models.TextChoices):
        ONLINE = 'Online', 'Online'
        OFFLINE = 'Offline', 'Offline'

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        CONFIRMED = 'Confirmed', 'Confirmed'
        CHECKED_IN = 'Checked In', 'Checked In'
        CHECKED_OUT = 'Checked Out', 'Checked Out'
        CANCELLED = 'Cancelled', 'Cancelled'
        EXPIRED = 'Expired', 'Expired'

    customer_id = models.ForeignKey('accounts.User', on_delete = models.PROTECT)
    hotel = models.ForeignKey("hotels.Hotel", on_delete= models.CASCADE)
    check_in_status = models.BooleanField(default=False)
    check_in = models.DateTimeField(auto_now_add = True)
    check_out_status = models.BooleanField(default=False)
    check_out = models.DateTimeField(auto_now_add = True)
    number_of_guests = models.PositiveIntegerField()
    status = models.CharField(max_length = 15, choices = StatusChoices.choices, default = StatusChoices.PENDING)
    booking_source = models.CharField(max_length = 15, choices = BookingSourceChoices.choices, default = BookingSourceChoices.ONLINE)
    special_requests = models.TextField(blank = True)
    subtotal = models.DecimalField(max_digits = 10, decimal_places = 2, default = 0.00)
    discount = models.DecimalField(max_digits = 10, decimal_places = 2, default = 0.00)
    tax = models.DecimalField(max_digits = 10, decimal_places = 2, default = 0.00)
    total = models.DecimalField(max_digits = 10, decimal_places = 2, default = 0.00)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)


class BookingRoom(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_rooms')
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    price_per_night = models.DecimalField(max_digits=10, decimal_places = 2)
    number_of_nights = models.PositiveIntegerField(default = 1)
    subtotal = models.DecimalField(max_digits=10, decimal_places = 2, default = 0.00)
    created_at = models.DateTimeField(auto_now_add = True)