# from django.db import models

# # Create your models here.


# class Order(models.Model):
    
#     class OrderStatusChoices(models.TextChoices):
#         PENDING = 'Pending', 'Pending'
#         ACCEPTED = 'Accepted', 'Accepted'
#         PREPARING = 'Preparing', 'Preparing'
#         READY = 'Ready', 'Ready'
#         DELIVERED = 'Delivered', 'Delivered'
#         CANCELLED = 'Cancelled', 'Cancelled'

#     booking = models.ForeignKey(
#         'bookings.Booking', 
#         on_delete = models.PROTECT, 
#         related_name = 'orders'
#     )

#     status = models.CharField(
#         max_length = 15, 
#         choices = OrderStatusChoices.choices, 
#         default = OrderStatusChoices.PENDING
#     )
#     subtotal = models.DecimalField(
#         max_digits = 10, 
#         decimal_places = 2, 
#         editable = False,
#     )
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     class Meta:
#         indexes = [
#             models.Index(fields = ['status', 'created_at']),
#         ]

#     def __str__(self):
#         return f'Order #{self.id} - {self.status}'

# class OrderItem(models.Model):
#     order = models.ForeignKey(
#         'Order', 
#         on_delete = models.PROTECT, 
#         related_name = 'items'
#     )
#     service = models.ForeignKey(
#         'Service', 
#         on_delete = models.CASCADE
#     )
#     quantity = models.PositiveIntegerField(default = 1)
#     unit_price = models.DecimalField(
#         max_digits = 10, 
#         decimal_places = 2
#     )
#     subtotal = models.DecimalField(
#         max_digits = 10, 
#         decimal_places = 2
#     )
#     created_at = models.DateTimeField(auto_now_add = True)


# class Service(models.Model):
#     class CategoryChoices(models.TextChoices):
#         ROOM_SERVICE = 'Room Service', 'Room Service'
#         HOUSEKEEPING = 'Housekeeping', 'Housekeeping'
#         LAUNDRY = 'Laundry', 'Laundry'
#         SPA = 'Spa', 'Spa'
#         GYM = 'Gym', 'Gym'
#         RESTAURANT = 'Restaurant', 'Restaurant'
#         BAR = 'Bar', 'Bar'
#         CONCIERGE = 'Concierge', 'Concierge'
#         TRANSPORTATION = 'Transportation', 'Transportation'
#         OTHER = 'Other', 'Other'

#     hotel = models.ForeignKey(
#         'hotels.Hotel', 
#         on_delete = models.CASCADE
#     )
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True)
#     category = models.CharField(
#         max_length=20, 
#         choices=CategoryChoices.choices, 
#         default=CategoryChoices.ROOM_SERVICE
#     )
#     custom_category_name = models.CharField(
#         max_length = 100, 
#         blank = True, 
#         null = True, 
#         help_text = "If 'Other' is selected as the category, please provide a custom category name."
#     )
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     def __str__(self):
#         return f'{self.name} [{self.get_category_display()}]'

# class SubServiceItem(models.Model):
#     service = models.ForeignKey(
#         'Service', 
#         on_delete = models.CASCADE, 
#         related_name = 'items'
#     )
#     name  = models.CharField(max_length = 255)
#     description = models.TextField(blank = True)
#     price = models.DecimalField(
#         max_digits = 10, 
#         decimal_places = 2
#     )
#     is_available = models.BooleanField(default = False)
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     def __str__(self):
#         return self.name



from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum


class Service(models.Model):
    class CategoryChoices(models.TextChoices):
        ROOM_SERVICE = 'ROOM_SERVICE', 'Room Service'
        HOUSEKEEPING = 'HOUSEKEEPING', 'Housekeeping'
        LAUNDRY = 'LAUNDRY', 'Laundry'
        SPA = 'SPA', 'Spa'
        GYM = 'GYM', 'Gym'
        RESTAURANT = 'RESTAURANT', 'Restaurant'
        BAR = 'BAR', 'Bar'
        CONCIERGE = 'CONCIERGE', 'Concierge'
        TRANSPORTATION = 'TRANSPORTATION', 'Transportation'
        OTHER = 'OTHER', 'Other'

    hotel = models.ForeignKey(
        'hotels.Hotel', 
        on_delete=models.CASCADE,
        related_name='services'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20, 
        choices=CategoryChoices.choices, 
        default=CategoryChoices.ROOM_SERVICE
    )
    custom_category_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Required if 'Other' is selected as the category."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.category == self.CategoryChoices.OTHER and not self.custom_category_name:
            raise ValidationError({'custom_category_name': "Custom category name is required when category is 'Other'."})

    def __str__(self):
        return f"{self.name} ({self.hotel})"


class SubServiceItem(models.Model):
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    booking = models.ForeignKey(
        'bookings.Booking', 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    status = models.CharField(
        max_length=15, 
        choices=OrderStatus.choices, 
        default=OrderStatus.PENDING
    )
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def update_subtotal(self, save=True):
        """Recalculate order subtotal from active items."""
        calculated = self.items.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')
        
        self.subtotal = calculated
        if save:
            super().save(update_fields=['subtotal', 'updated_at'])
            # Trigger total sync on parent Booking
            if hasattr(self.booking, 'recalculate_totals'):
                self.booking.recalculate_totals(save=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    item = models.ForeignKey(
        SubServiceItem, 
        on_delete=models.PROTECT,
        related_name='order_items',
    
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        editable=False
    )
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.item and not self.item.is_available:
            raise ValidationError({'item': 'This service item is currently unavailable.'})

        # Ensure item belongs to the same hotel as the booking
        if self.item and self.order_id and hasattr(self.order, 'booking'):
            if self.item.service.hotel_id != self.order.booking.hotel_id:
                raise ValidationError({'item': 'Selected item does not belong to the booking hotel.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Snapshot the current price from SubServiceItem
        if not self.unit_price and self.item:
            self.unit_price = self.item.price

        self.subtotal = (self.unit_price * self.quantity).quantize(Decimal('0.01'))

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.order.update_subtotal(save=True)

    def __str__(self):
        return f"{self.quantity}x {self.item.name} (Order #{self.order_id})"