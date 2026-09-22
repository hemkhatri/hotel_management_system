from django.contrib import admin
from .models import Hotel, Amenity, RoomCategory


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "address", "created_at")
    search_fields = ("name", "email", "phone", "address")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "description")
        }),
        ("Contact & Location", {
            "fields": ("email", "phone", "address")
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(RoomCategory)
class RoomCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "base_price", "max_occupancy", "created_at")
    list_filter = ("status", "max_occupancy", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
    
    # Enable the horizontal filter widget for ManyToMany relation selection
    filter_horizontal = ("amenities",)
    
    fieldsets = (
        ("Category Details", {
            "fields": ("name", "description", "status")
        }),
        ("Pricing & Capacity", {
            "fields": ("base_price", "max_occupancy")
        }),
        ("Features", {
            "fields": ("amenities",)
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )
