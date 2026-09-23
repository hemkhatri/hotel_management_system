from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum, Q

# Create your models here.
class Booking(models.Model):
    class BookingSourceChoices(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        OFFLINE = 'OFFLINE', 'Offline'

    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'  
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    customer_id = models.ForeignKey('accounts.User', on_delete = models.PROTECT, related_name = 'bookings')
    hotel = models.ForeignKey("hotels.Hotel", on_delete= models.CASCADE)

    check_in = models.DateTimeField()
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
        default = Decimal('0.00'), 
        editable = False
    )
    discount = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal('0.00')
    )
    tax = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal('0.00')
    )    
    total = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = Decimal('0.00'),
        editable = False
    )
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def clean(self):
        super().clean()
        if (self.check_in and self.check_out) and (self.check_out <= self.check_in):
            raise ValidationError({'check_out': 'Check-out date must be after check-in date.'})
        
    def update_totals(self, save = True):
        # this will total all the room base price 
        rooms_subtotal = self.booking_rooms.aggregate(
            total = Sum('subtotal')
            )['total'] or Decimal('0.00')

        # this will calculate all the total servies that user did on hotel like food or services
        orders_subtotal = self.orders.exclude(
            status = 'CANCELLED'
            ).aggregate(
                total = Sum('subtotal')
            )['total'] or Decimal('0.00')
        self.subtotal = rooms_subtotal + orders_subtotal
        calculated_total = self.subtotal - self.discount + self.tax
        self.total = max(Decimal('0.00'), calculated_total)

        if save:
            super().save(update_fields = ['subtotal', 'total', 'updated_at'])

    def save(self, *args, **kwargs):
        self.full_clean()
        calculated_total = self.subtotal - self.discount + self.tax
        self.total = max(Decimal('0.00'), calculated_total)
        # if self.pk:
        #     self.total = self.subtotal - self.discount + self.tax
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Booking #{self.id} - {self.customer_id}"
    
class BookingRoom(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_rooms')
    room = models.ForeignKey(
        'rooms.Room', 
        on_delete=models.CASCADE,
        related_name = 'booking_rooms'
    )
    price_per_night = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        editable = False
    )
    number_of_nights = models.PositiveIntegerField(default = 1)
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places = 2, 
        editable = False
    )
    created_at = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        if not self.price_per_night and self.room:
            self.price_per_night = self.room.category.base_price
        self.subtotal = (self.price_per_night * self.number_of_nights).quantize(Decimal("0.01"))

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.booking.update_totals(save = True)

    def __str__(self):
        return f"Room {self.room.room_number} for Booking #{self.booking.id}"




# from decimal import Decimal
# from django.core.exceptions import ValidationError
# from django.db import models, transaction
# from django.db.models import Q, Sum


# class Booking(models.Model):
#     class BookingSource(models.TextChoices):
#         ONLINE = 'ONLINE', 'Online'
#         OFFLINE = 'OFFLINE', 'Offline'

#     class Status(models.TextChoices):
#         PENDING = 'PENDING', 'Pending'
#         CONFIRMED = 'CONFIRMED', 'Confirmed'
#         CHECKED_IN = 'CHECKED_IN', 'Checked In'
#         CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
#         CANCELLED = 'CANCELLED', 'Cancelled'
#         EXPIRED = 'EXPIRED', 'Expired'

#     customer = models.ForeignKey(
#         'accounts.User',
#         on_delete=models.PROTECT,
#         related_name='bookings'
#     )
#     hotel = models.ForeignKey(
#         "hotels.Hotel",
#         on_delete=models.CASCADE,
#         related_name='bookings'
#     )

#     check_in = models.DateTimeField()
#     check_out = models.DateTimeField()
#     number_of_guests = models.PositiveIntegerField()

#     status = models.CharField(
#         max_length=15,
#         choices=Status.choices,
#         default=Status.PENDING
#     )
#     booking_source = models.CharField(
#         max_length=15,
#         choices=BookingSource.choices,
#         default=BookingSource.ONLINE
#     )
#     special_requests = models.TextField(blank=True)

#     subtotal = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=Decimal('0.00'),
#         editable=False
#     )
#     discount = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=Decimal('0.00')
#     )
#     tax = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=Decimal('0.00')
#     )
#     total = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=Decimal('0.00'),
#         editable=False
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def clean(self):
#         super().clean()
#         if self.check_in and self.check_out and self.check_out <= self.check_in:
#             raise ValidationError({'check_out': 'Check-out date must be after check-in date.'})

#     def recalculate_totals(self, save=True):
#         """Atomic recalculation of subtotal and total balance."""
#         rooms_subtotal = self.booking_rooms.aggregate(
#             total=Sum('subtotal')
#         )['total'] or Decimal('0.00')

#         # Assuming Order model has an OrderStatus or similar text choices
#         orders_subtotal = self.orders.exclude(
#             status='CANCELLED'
#         ).aggregate(
#             total=Sum('subtotal')
#         )['total'] or Decimal('0.00')

#         self.subtotal = rooms_subtotal + orders_subtotal
#         calculated_total = self.subtotal - self.discount + self.tax
#         self.total = max(Decimal('0.00'), calculated_total)

#         if save:
#             super().save(update_fields=['subtotal', 'total', 'updated_at'])

#     def save(self, *args, **kwargs):
#         self.full_clean()
#         calculated_total = self.subtotal - self.discount + self.tax
#         self.total = max(Decimal('0.00'), calculated_total)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"Booking #{self.id} - {self.customer}"


# class BookingRoom(models.Model):
#     booking = models.ForeignKey(
#         Booking,
#         on_delete=models.CASCADE,
#         related_name='booking_rooms'
#     )
#     room = models.ForeignKey(
#         'rooms.Room',
#         on_delete=models.CASCADE,
#         related_name='booking_rooms'
#     )
#     price_per_night = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         editable=False
#     )
#     number_of_nights = models.PositiveIntegerField(default=1)
#     subtotal = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         editable=False
#     )
#     created_at = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         if not self.price_per_night and self.room:
#             self.price_per_night = self.room.category.base_price

#         self.subtotal = (self.price_per_night * self.number_of_nights).quantize(Decimal('0.01'))

#         with transaction.atomic():
#             super().save(*args, **kwargs)
#             # Update parent booking total atomically
#             self.booking.recalculate_totals(save=True)

#     def __str__(self):
#         return f"Room {self.room} for Booking #{self.booking_id}"