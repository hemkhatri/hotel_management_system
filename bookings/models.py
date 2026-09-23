from django.db import models
from django.db.models import Sum
from decimal import Decimal
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
    check_in = models.DateTimeField()
    check_out_status = models.BooleanField(default=False)
    check_out = models.DateTimeField()

    number_of_guests = models.PositiveIntegerField()
    status = models.CharField(
        max_length = 15, 
        choices = StatusChoices.choices, 
        default = StatusChoices.PENDING
    )
    booking_source = models.CharField(
        max_length = 15, 
        choices = BookingSourceChoices.choices, 
        default = BookingSourceChoices.ONLINE
    )
    special_requests = models.TextField(blank = True)
    subtotal = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal(0.00), 
        editable = False
    )
    discount = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal(0.00)
    )
    tax = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal(0.00)
    )    
    total = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal(0.00),
        editable = False
    )
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def update_totals(self):
        # this will total all the room base price 
        rooms_subtotal = self.booking_rooms.aggregate(
            total = Sum('subtotal')
            )['total'] or Decimal(0.00)

        # this will calculate all the total serives that user did on hotel like food or services
        orders_subtotal = self.orders.exclude(
            status = 'Cancelled'
            ).aggregate(
                total = Sum('subtotal')
            )['total'] or Decimal(0.00)
        self.subtotal = rooms_subtotal + orders_subtotal
        self.total = self.subtotal - self.discount + self.tax

        super().save(update_fields = ['subtotal', 'total', 'updated_at'])

    def save(self, *args, **kwargs):
        if self.pk:
            self.total = self.subtotal - self.discount + self.tax
        super().save(*args, **kwargs)


    # def save(self, *args, **kwargs):
    #     self.price_per_night = self.room.category.base_price
    #     self.subtotal = self.price_per_night * self.number_of_nights
    #     super().save(*args, **kwargs)
    #     self.booking.update_total()

    def save(self, *args, **kwargs):
        # REMOVED: self.price_per_night = self.room.category.base_price  <-- THIS WAS CAUSING THE BUG
        
        # Recalculate total if an existing booking's discount/tax is updated
        if self.pk:
            self.total = self.subtotal - self.discount + self.tax
        super().save(*args, **kwargs)


    # def __str__(self):
    #     return self.id
    
class BookingRoom(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_rooms')
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    price_per_night = models.DecimalField(max_digits=10, decimal_places = 2, blank = True)
    number_of_nights = models.PositiveIntegerField(default = 1)
    subtotal = models.DecimalField(max_digits=10, decimal_places = 2, default = Decimal(0.00), editable = False)
    created_at = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        if not self.price_per_night:
            self.price_per_night = self.room.category.base_price

        self.subtotal = self.price_per_night * self.number_of_nights
        super().save(*args, **kwargs)
        self.booking.update_totals()

    def __str__(self):
        return f"Room {self.room.room_number} for Booking #{self.booking.id}"