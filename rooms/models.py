from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

# rooms/models.py
class Room(models.Model):
    class RoomStatusChoices(models.TextChoices):
        AVAILABLE = 'Available', 'Available'
        OCCUPIED = 'Occupied', 'Occupied'
        MAINTENANCE = 'Maintenance', 'Maintenance'
        RESERVED = 'Reserved', 'Reserved'

    category = models.ForeignKey('hotels.RoomCategory', on_delete = models.CASCADE)
    room_number = models.CharField(max_length = 20)
    floor = models.PositiveIntegerField(validators = [MinValueValidator(0), MaxValueValidator(10)])
    description = models.TextField(blank = True)
    status = models.CharField(max_length = 15, choices = RoomStatusChoices.choices, default = RoomStatusChoices.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.room_number

class RoomMedia(models.Model):
    room = models.ForeignKey(Room, on_delete = models.CASCADE)
    media_type = models.CharField(max_length = 10, choices = [('image', 'Image'), ('video', 'Video')])
    caption = models.TextField(blank = True)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.room.room_number  # Changed from self.room.name to self.room.room_number for clarity

    # this helps to sort media to come first video and then images with the created date 
    class Meta:
        ordering = ['-media_type', 'created_at']
