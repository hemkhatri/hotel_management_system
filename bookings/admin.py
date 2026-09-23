# # bookings/admin.py
# from decimal import Decimal
# from django import forms
# from django.contrib import admin
# from django.db import transaction
# from .models import Booking, BookingRoom
# from services.models import Order, OrderItem, SubServiceItem


# # ==========================================
# # Forms & Dynamic Options
# # ==========================================

# class OrderItemInlineForm(forms.ModelForm):
#     """
#     Custom form for inline OrderItem selection.
#     Restricts selection to available SubServiceItems.
#     """
#     class Meta:
#         model = OrderItem
#         fields = "__all__"

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Filter dropdown to show only available sub-services
#         if "item" in self.fields:
#             self.fields["item"].queryset = SubServiceItem.objects.filter(
#                 is_available=True
#             ).select_related("service")
#             self.fields["item"].label = "Service Item (e.g. Restaurant -> Food)"


# # ==========================================
# # Inlines
# # ==========================================

# class BookingRoomInline(admin.TabularInline):
#     model = BookingRoom
#     extra = 0
#     readonly_fields = ("price_per_night", "subtotal", "created_at")
#     fields = ("room", "price_per_night", "number_of_nights", "subtotal")


# class OrderItemNestedInline(admin.TabularInline):
#     """
#     Allows adding specific consumable items (Food, Spa, Laundry)
#     directly under an Order.
#     """
#     model = OrderItem
#     form = OrderItemInlineForm
#     extra = 1
#     fields = ("item", "quantity", "unit_price", "subtotal")
#     readonly_fields = ("unit_price", "subtotal")


# class OrderInline(admin.TabularInline):
#     """
#     Displays service orders attached to the booking.
#     Staff can set status to 'PENDING' when creating service requests.
#     """
#     model = Order
#     extra = 1
#     fields = ("status", "subtotal", "created_at")
#     readonly_fields = ("subtotal", "created_at")
#     show_change_link = True


# # ==========================================
# # Model Admin Configurations
# # ==========================================

# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "customer_id",
#         "hotel",
#         "status",
#         "booking_source",
#         "subtotal",
#         "discount",
#         "tax",
#         "total",
#         "check_in",
#         "check_out",
#     )
#     list_filter = ("status", "booking_source", "created_at", "hotel")
#     search_fields = (
#         "id",
#         "customer_id__username",
#         "customer_id__email",
#         "hotel__name",
#     )
#     date_hierarchy = "created_at"
#     readonly_fields = ("subtotal", "total", "created_at", "updated_at")
#     inlines = [BookingRoomInline, OrderInline]

#     fieldsets = (
#         ("Target Information", {"fields": ("customer_id", "hotel", "number_of_guests")}),
#         (
#             "Status & Metadata",
#             {"fields": ("status", "booking_source", "check_in", "check_out")},
#         ),
#         ("Financial Breakdown", {"fields": (("subtotal", "discount", "tax"), "total")}),
#         ("Additional Notes", {"classes": ("collapse",), "fields": ("special_requests",)}),
#         ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
#     )

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("customer_id", "hotel")

#     @transaction.atomic
#     def save_related(self, request, form, formsets, change):
#         """
#         Saves inline items first, then executes atomic total updates across models.
#         """
#         super().save_related(request, form, formsets, change)
#         booking = form.instance
        
#         # Trigger total recalculations across linked orders and booking rooms
#         if hasattr(booking, "recalculate_totals"):
#             booking.recalculate_totals(save=True)
#         elif hasattr(booking, "update_totals"):
#             booking.update_totals()


# @admin.register(BookingRoom)
# class BookingRoomAdmin(admin.ModelAdmin):
#     list_display = ("id", "booking", "room", "price_per_night", "number_of_nights", "subtotal")
#     list_filter = ("created_at",)
#     search_fields = ("booking__id", "room__room_number")
#     readonly_fields = ("price_per_night", "subtotal", "created_at")

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("booking", "room")




# bookings/admin.py
from django.contrib import admin
from django.db import transaction

from .models import Booking, BookingRoom
from services.models import Order


# ==========================================
# Inlines
# ==========================================

class BookingRoomInline(admin.TabularInline):
    model = BookingRoom
    extra = 0
    readonly_fields = ("price_per_night", "subtotal", "created_at")
    fields = ("room", "price_per_night", "number_of_nights", "subtotal")


class OrderInline(admin.TabularInline):
    """
    Shows attached Orders under Booking.
    'show_change_link = True' displays a direct link next to each Order
    taking staff directly to OrderAdmin to manage OrderItems.
    """
    model = Order
    extra = 1
    fields = ("status", "subtotal", "created_at")
    readonly_fields = ("subtotal", "created_at")
    show_change_link = True


# ==========================================
# Booking Admin
# ==========================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_id",  # Fixed: Restored to customer_id to match your Booking model field
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
    readonly_fields = ("subtotal", "total", "created_at", "updated_at")
    inlines = [BookingRoomInline, OrderInline]

    fieldsets = (
        ("Target Information", {"fields": ("customer_id", "hotel", "number_of_guests")}),
        (
            "Status & Metadata",
            {"fields": ("status", "booking_source", "check_in", "check_out")},
        ),
        ("Financial Breakdown", {"fields": (("subtotal", "discount", "tax"), "total")}),
        ("Additional Notes", {"classes": ("collapse",), "fields": ("special_requests",)}),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("customer_id", "hotel")

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        booking = form.instance

        if hasattr(booking, "recalculate_totals"):
            booking.recalculate_totals(save=True)


@admin.register(BookingRoom)
class BookingRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "room", "price_per_night", "number_of_nights", "subtotal")
    list_filter = ("created_at",)
    search_fields = ("booking__id", "room__room_number")
    readonly_fields = ("price_per_night", "subtotal", "created_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("booking", "room")