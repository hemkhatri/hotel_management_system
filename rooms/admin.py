from django.contrib import admin
from .models import Room, RoomMedia


class RoomMediaInline(admin.TabularInline):
    model = RoomMedia
    extra = 1
    readonly_fields = ("created_at",)
    fields = ("media_type", "caption", "created_at")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    # Quick view configuration
    list_display = ("room_number", "category", "floor", "status", "created_at")
    list_filter = ("status", "floor", "category", "created_at")
    search_fields = ("room_number", "category__name", "description")
    date_hierarchy = "created_at"

    # Form structure
    fieldsets = (
        (
            "Room Assignment",
            {
                "fields": ("room_number", "category", "floor"),
            },
        ),
        (
            "Availability",
            {
                "fields": ("status",),
            },
        ),
        (
            "Details",
            {
                "fields": ("description",),
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    # Manage images/videos directly inside the room view
    inlines = [RoomMediaInline]


@admin.register(RoomMedia)
class RoomMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "room_display", "media_type", "caption", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("room__room_number", "caption")
    readonly_fields = ("created_at",)

    @admin.display(description="Room")
    def room_display(self, obj):
        return f"Room {obj.room.room_number}"


# ⚠️ Quick Note on RoomMedia's __str__ method:
# Your current models.py has `return self.room.name` inside RoomMedia.__str__.
# However, the Room model doesn't have a 'name' field (it uses 'room_number').
# To prevent an AttributeError in your Django admin, consider updating that method in your models.py to:
#
# def __str__(self):
#     return f"{self.media_type.capitalize()} for Room {self.room.room_number}"
