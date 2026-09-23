from django.db import models

# Create your models here.


class Order(models.Model):
    
    class OrderStatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        ACCEPTED = 'Accepted', 'Accepted'
        PREPARING = 'Preparing', 'Preparing'
        READY = 'Ready', 'Ready'
        DELIVERED = 'Delivered', 'Delivered'
        CANCELLED = 'Cancelled', 'Cancelled'

    booking = models.ForeignKey(
        'bookings.Booking', 
        on_delete = models.PROTECT, 
        related_name = 'orders'
    )

    status = models.CharField(
        max_length = 15, 
        choices = OrderStatusChoices.choices, 
        default = OrderStatusChoices.PENDING
    )
    subtotal = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2, 
        default = 0.00
    )
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        indexes = [
            models.Index(fields = ['status', 'created_at']),
        ]

    def __str__(self):
        return f'Order #{self.id} - {self.status}'

class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order', 
        on_delete = models.CASCADE, 
        related_name = 'items'
    )
    service = models.ForeignKey(
        'Service', 
        on_delete = models.CASCADE
    )
    quantity = models.PositiveIntegerField(default = 1)
    unit_price = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2
    )
    subtotal = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2
    )
    created_at = models.DateTimeField(auto_now_add = True)


class Service(models.Model):
    class CategoryChoices(models.TextChoices):
        ROOM_SERVICE = 'Room Service', 'Room Service'
        HOUSEKEEPING = 'Housekeeping', 'Housekeeping'
        LAUNDRY = 'Laundry', 'Laundry'
        SPA = 'Spa', 'Spa'
        GYM = 'Gym', 'Gym'
        RESTAURANT = 'Restaurant', 'Restaurant'
        BAR = 'Bar', 'Bar'
        CONCIERGE = 'Concierge', 'Concierge'
        TRANSPORTATION = 'Transportation', 'Transportation'
        OTHER = 'Other', 'Other'

    hotel = models.ForeignKey(
        'hotels.Hotel', 
        on_delete = models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20, 
        choices=CategoryChoices.choices, 
        default=CategoryChoices.ROOM_SERVICE
    )
    custom_category_name = models.CharField(
        max_length = 100, 
        blank = True, 
        null = True, 
        help_text = "If 'Other' is selected as the category, please provide a custom category name."
    )
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'{self.name} [{self.get_category_display()}]'

class SubServiceItem(models.Model):
    service = models.ForeignKey(
        'Service', 
        on_delete = models.CASCADE, 
        related_name = 'items'
    )
    name  = models.CharField(max_length = 255)
    description = models.TextField(blank = True)
    price = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2
    )
    is_available = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name





# this is from gemini.com

# from django.db import models
# from django.core.exceptions import ValidationError

# class Order(models.Model):
#     class OrderStatusChoices(models.TextChoices):
#         PENDING = 'Pending', 'Pending'
#         ACCEPTED = 'Accepted', 'Accepted'
#         PREPARING = 'Preparing', 'Preparing'
#         READY = 'Ready', 'Ready'
#         DELIVERED = 'Delivered', 'Delivered'
#         CANCELLED = 'Cancelled', 'Cancelled'

#     # Booking is the single source of truth for room and user
#     booking = models.ForeignKey('bookings.Booking', on_delete=models.PROTECT, related_name='orders')
#     status = models.CharField(max_length=15, choices=OrderStatusChoices.choices, default=OrderStatusChoices.PENDING)
#     total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         indexes = [
#             models.Index(fields=['status', 'created_at']),
#         ]

#     def __str__(self):
#         return f'Order #{self.pk} - {self.status}'


# class ServiceCategory(models.Model):
#     hotel = models.ForeignKey('hotels.Hotel', on_delete=models.CASCADE, related_name='service_categories')
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name


# class ServiceItem(models.Model):
#     '''Represents an actual orderable menu item or service product'''
#     category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name='items')
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     is_available = models.BooleanField(default=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f'{self.name} (${self.price})'


# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
#     # Point directly to the exact menu/service item being purchased
#     service_item = models.ForeignKey(ServiceItem, on_delete=models.PROTECT)
#     quantity = models.PositiveIntegerField(default=1)
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2) # Snapshotted at purchase time
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
#     created_at = models.DateTimeField(auto_now_add=True)

#     def clean(self):
#         super().clean()
#         if self.quantity < 1:
#             raise ValidationError('Quantity must be at least 1.')

#     def save(self, *args, **kwargs):
#         # Auto-calculate subtotal to prevent manual calculation bugs
#         self.subtotal = self.quantity * self.unit_price
#         super().save(*args, **kwargs)