from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Hotel(models.Model):
    name = models.CharField(max_length = 100)
    address = models.CharField(max_length = 200)
    no_of_floor = models.PositiveIntegerField(
        default = 0,
        validators = [
            MinValueValidator(0),
            MaxValueValidator(10),
            ]
        )
    email = models.EmailField(max_length = 20)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length = 100)
    descripiton = models.TextField(blank = True, null = True)

    def __str__(self):
        return self.name

class RoomCategory(models.Model):
    class CategoryStatusChoices(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DRAFT = 'DRAFT', 'Draft'
        ARCHIVED = 'ARCHIVED', 'Archived'
        HIDDEN = 'HIDDEN', 'Hidden'

    amenities = models.ManyToManyField(
        Amenity, 
        blank = True
        )
    name = models.CharField(max_length = 20)
    description = models.TextField(
        blank = True, 
        null = True
        )
    base_price = models.DecimalField(
        max_digits = 10, 
        decimal_places = 2
        )
    max_occupancy = models.PositiveIntegerField(
        default = 1, 
        validators = [
            MaxValueValidator(10),
            MinValueValidator(1)
            ]
        )
    status = models.CharField(
        max_length = 20,
        choices = CategoryStatusChoices,
        default = CategoryStatusChoices.DRAFT,
        )
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name
    
