from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

# hotel basic details
class Hotel(models.Model):
    name = models.CharField(max_length = 100)
    address = models.CharField(max_length =  200)
    phone = models.CharField(max_length = 10)
    email = models.EmailField(max_length = 20)
    description = models.TextField(max_length = 500)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name

# Hotel Amenities
class Amenity(models.Model):
    name = models.CharField(max_length = 100)


class RoomCategoryStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    DRAFT = 'Draft', 'Draft'
    ARCHIVED = 'Archived', 'Archived'
    HIDDEN = 'Hidden', 'Hidden'


# Room Category
class RoomCategory(models.Model):
    name = models.CharField(max_length = 100)
    description = models.TextField(max_length = 500)
    base_price = models.DecimalField(max_digits = 10, decimal_places = 2)
    max_occupancy = models.PositiveIntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    amenities = models.ManyToManyField(Amenity, blank = True)
    status = models.CharField(max_length = 15, choices = RoomCategoryStatus.choices, default = RoomCategoryStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name