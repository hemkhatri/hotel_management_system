from django.contrib import admin
from .models import Booking, BookingRoom


class BookingRoomInline(admin.TabularInline):
    model = BookingRoom
    extra = 0
    readonly_fields = ("subtotal", "created_at")
    fields = ("room", "price_per_night", "number_of_nights", "subtotal")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Core layout configuration
    list_display = (
        "id",
        "customer_id",
        "hotel",
        "status",
        "booking_source",
        "total",
        "check_in",
        "check_out",
    )
    list_filter = ("status", "booking_source", "created_at", "hotel")
    search_fields = (
        "id",
        "customer_id__username",
        "customer_id__email",
        "hotel__name",
    )
    date_hierarchy = "created_at"

    # Admin form structure
    fieldsets = (
        (
            "Target Information",
            {"fields": ("customer_id", "hotel", "number_of_guests")},
        ),
        (
            "Status & Metadata",
            {
                "fields": (
                    "status",
                    "booking_source",
                    ("check_in_status", "check_in"),
                    ("check_out_status", "check_out"),
                )
            },
        ),
        (
            "Financial Breakdown",
            {"fields": (("subtotal", "discount", "tax"), "total")},
        ),
        (
            "Additional Notes",
            {"classes": ("collapse",), "fields": ("special_requests",)},
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )

    # Prevent accidental overwrites of auto fields
    readonly_fields = ("created_at", "updated_at", "check_in", "check_out")

    # Display associated rooms inline inside the Booking view
    inlines = [BookingRoomInline]


@admin.register(BookingRoom)
class BookingRoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "room",
        "price_per_night",
        "number_of_nights",
        "subtotal",
    )
    list_filter = ("created_at",)
    search_fields = ("booking__id", "room__room_number")
    readonly_fields = ("created_at",)
