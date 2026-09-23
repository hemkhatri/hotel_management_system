# bookings/admin.py
from django.contrib import admin
from .models import Booking, BookingRoom
from services.models import Order  # Import Order from services app


class BookingRoomInline(admin.TabularInline):
    model = BookingRoom
    extra = 0
    readonly_fields = ("subtotal", "created_at", 'price_per_night')  # Added 'price_per_night' to readonly_fields
    fields = ("room", "price_per_night", "number_of_nights", "subtotal")


class OrderInline(admin.TabularInline):
    """Allows staff to view attached food/service orders within the Booking page."""
    model = Order
    extra = 0
    readonly_fields = ("status", "subtotal", "created_at")  # Changed 'total' -> 'subtotal'
    fields = ("id", "status", "subtotal", "created_at")      # Changed 'total' -> 'subtotal'
    show_change_link = True
    can_delete = False

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Core layout configuration
    list_display = (
        "id",
        "customer_id",
        "hotel",
        "status",
        "booking_source",
        "subtotal",
        "discount",
        "tax",
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

    # Optimize list query performance
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("customer_id", "hotel")

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
                    ("check_in"),
                    ("check_out"),
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

    # Note: check_in and check_out removed from readonly_fields so staff can edit reservation dates
    readonly_fields = (
        "subtotal", 
        "total", 
        "created_at", 
        "updated_at", 
    )

    # Display associated rooms and orders inline inside the Booking view
    inlines = [BookingRoomInline, OrderInline]

    def save_related(self, request, form, formsets, change):
        """Forces total recalculation after inline items (rooms/orders) are updated."""
        super().save_related(request, form, formsets, change)
        form.instance.update_totals()


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
    readonly_fields = ("subtotal", "created_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("booking", "room")