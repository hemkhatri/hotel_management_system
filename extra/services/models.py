from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum

class Service(models.Model):
    class CategoryChoices(models.TextChoices):
        ROOM_SERVICE = 'ROOM_SERVICE', 'Room Service'
        HOUSEKEEPING = 'HOUSEKEEPING', 'House Keeping'
        LAUNDRY = 'LAUNDRY', 'Laundry'
        SPA = 'SPA', 'SPA'
        GYM = 'GYM', 'Gym'
        RESTAURANT = 'RESTAURANT', 'Restaurant'
        BAR = 'BAR', 'Bar'
        TRANSPORTATION = 'TRANSPORTATION', 'Transportation'
        OTHER = 'OTHER', 'Other'
    hotel = models.ForeignKey(
        'hotels.Hotel',
        on_delete = models.CASCADE,
        related_name = 'services'
    )
    name = models.CharField(max_length = 200)
    description = models.TextField(blank = True)
    category = models.CharField(
        max_length = 20,
        choices = CategoryChoices,
        default = CategoryChoices.ROOM_SERVICE
    )
    custom_category_name = models.CharField(
        max_length = 20,
        blank = True,
        null = True,
        help_text = "Required if 'Other' is selected as category"
    )
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def clean(self):
        super().clean()
        if self.category == self.CategoryChoices.OTHER and not self.custom_category_name:
            raise ValidationError({'custom_category_name': "Custom Category is required when category is select 'Other'"})


        if self.category != self.CategoryChoices.OTHER and self.custom_category_name:
            raise ValidationError({'custom_category_name': "Custom Category is only need when category is select 'Other'"})

    def __str__(self):
        return self.name

class SubServicesItem(models.Model):
    service = models.ForeignKey(
        'Service', 
        on_delete = models.CASCADE,
        related_name = 'items'
    )
    name = models.CharField(max_length = 255)
    description = models.TextField(blank = True)
    price = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2
    )
    is_avilable = models.BooleanField(
        default = True
    )
    created_at = models.DateTimeField(
        auto_now_add = True
    )
    updated_at = models.DateTimeField(
        auto_now = True
    )

    def __str__(self):
        return self.name

class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete = models.PROTECT,
        related_name = 'orders',
    )
    status = models.CharField(
        max_length = 15,
        choices = StatusChoices,
        default = StatusChoices.PENDING
    )
    subtotal = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        editable = False,
        default = Decimal('0.00'),
    )
    created_at = models.DateTimeField(
        auto_now_add = True
    )
    updated_at = models.DateTimeField(
        auto_now = True
    )

    def update_subtotal(self, save = True):
        calculated = self.items.aggregate(
            total = Sum('subtotal')
        )['total'] or Decimal('0.00')

        self.subtotal = calculated
        if save:
            super().save(update_fields = ['subtotal', 'updated_at'])
            if hasattr(self.booking, 'update_subtotals'):
                self.booking.update_subtotals(save = True)

    def __str__(self):
        return f"Order #{self.id} -- {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order',
        on_delete = models.CASCADE,
        related_name = 'items'
    )
    item = models.ForeignKey(
        'services.SubServicesItem',
        on_delete = models.CASCADE,
        related_name = 'order_items',
    )
    quantity = models.PositiveIntegerField(default = 1)
    unit_price = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        editable = False,
    )
    subtotal = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        editable = False,
    )
    created_at = models.DateTimeField(auto_now_add = True)

    def clean(self):
        super().clean()
        if self.item and not self.item.is_avilable:
            raise ValidationError({
                'item': 'This service item is currently unavilable',
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        # snapshot of current price 
        if not self.unit_price and self.item:
            self.unit_price = self.item.price

        self.subtotal = (self.unit_price * self.quantity).quantize(Decimal('0.01'))

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.order.update_subtotal(save = True)