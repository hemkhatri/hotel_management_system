# from django.contrib import admin
# from django.db import transaction
# from .models import Booking, BookingRoom

# # =====================================================================
# # 1. BOOKING ROOM INLINE INTERFACE
# # =====================================================================
# class BookingRoomInline(admin.TabularInline):
#     model = BookingRoom
#     extra = 1
#     # subtotal_room and available_date are auto-calculated, lock them in the UI
#     readonly_fields = ['subtotal_room', 'available_date']
#     fields = ['room', 'booked_price', 'number_of_nights', 'subtotal_room', 'available_date']


# # =====================================================================
# # 2. BOOKING ADMIN CONFIGURATION
# # =====================================================================
# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     # Columns shown in the main table overview
#     list_display = [
#         'id', 'user', 'hotel', 'check_in', 'check_out', 
#         'status', 'subtotal', 'order_total', 'total', 'created_at'
#     ]
    
#     # Left sidebar dynamic filters
#     list_filter = ['status', 'booking_source', 'hotel', 'check_in', 'check_out']
    
#     # Quick search indices (supports drilling into related models)
#     search_fields = ['id', 'user__username', 'user__email', 'hotel__name', 'special_request']
    
#     # Financial fields are auto-managed by your model calculation routines
#     readonly_fields = ['subtotal', 'order_total', 'discount', 'tax', 'total']
    
#     # Grid groupings for clean form organization
#     fieldsets = (
#         ('Core Details', {
#             'fields': ('user', 'hotel', 'status', 'booking_source')
#         }),
#         ('Stay Schedule', {
#             'fields': (('check_in', 'check_in_status'), ('check_out', 'check_out_status'), 'special_request')
#         }),
#         ('Tax & Discount Adjustments', {
#             'fields': (('discount_percentage', 'discount'), ('tax_percentage', 'tax'))
#         }),
#         ('Financial Breakdown Overview', {
#             'classes': ('collapse',),  # Collapsible by default
#             'fields': ('subtotal', 'order_total', 'total')
#         }),
#     )

#     inlines = [BookingRoomInline]

#     def save_model(self, request, obj, form, change):
#         """Forces custom model clean constraints to throw clean admin interface warnings."""
#         obj.full_clean()
#         super().save_model(request, obj, form, change)

#     def save_formset(self, request, form, formset, change):
#         """
#         Runs atomic aggregation directly after inline room blocks are modified or
#         added by an administrator, updating the overarching balance columns.
#         """
#         with transaction.atomic():
#             formset.save()
#             form.instance.update_subtotals(save=True)

#     def delete_model(self, request, obj):
#         """Ensures deletions handle safe cancellation logic if necessary."""
#         super().delete_model(request, obj)


from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import BaseInlineFormSet
from .models import Booking, BookingRoom


# =====================================================================
# 1. BOOKING ROOM INLINE INTERFACE
# =====================================================================
# class BookingRoomInlineFormSet(BaseInlineFormSet):
#     def clean(self):
#         """
#         Validates total room occupancy against the total guests in the admin panel
#         before any database records are written.
#         """
#         super().clean()
        
#         # Don't validate if the main booking form has errors
#         if not self.instance or any(form.errors for form in self.forms):
#             return

#         # FIXED: updated field name to 'number_of_guests'
#         total_guests = getattr(self.instance, 'number_of_guests', 1)
#         total_capacity = 0
#         active_rooms_exist = False

#         for form in self.forms:
#             # Skip empty forms or forms marked for deletion
#             if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
#                 continue
            
#             room = form.cleaned_data.get('room')
#             if room and hasattr(room, 'category'):
#                 active_rooms_exist = True
#                 total_capacity += room.category.max_occupancy

#         # Only apply constraint if rooms are attached to this formset submission
#         if active_rooms_exist and total_guests > total_capacity:
#             raise ValidationError(
#                 f"This booking is for {total_guests} guests, but the selected "
#                 f"room(s) only accommodate up to {total_capacity} guests. "
#                 f"Please add more rooms or adjust guest counts."
#             )

class BookingRoomInlineFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        if not self.instance or any(form.errors for form in self.forms):
            return

        total_guests = getattr(self.instance, 'number_of_guests', 1)
        total_capacity = 0
        active_rooms_exist = False

        # ---------------------------------------------------------
        # 1. Validate room capacity
        # ---------------------------------------------------------
        for form in self.forms:

            if not form.cleaned_data:
                continue

            if form.cleaned_data.get('DELETE', False):
                continue

            room = form.cleaned_data.get('room')

            if room and hasattr(room, 'category'):
                active_rooms_exist = True
                total_capacity += room.category.max_occupancy

        if active_rooms_exist and total_guests > total_capacity:
            raise ValidationError(
                f"This booking is for {total_guests} guests, "
                f"but the selected room(s) only accommodate "
                f"up to {total_capacity} guests. "
                f"Please add more rooms or adjust guest counts."
            )

        # ---------------------------------------------------------
        # 2. Validate room availability
        # ---------------------------------------------------------
        check_in = self.instance.check_in
        check_out = self.instance.check_out

        if not check_in or not check_out:
            return

        active_statuses = [
            Booking.StatusChoices.PENDING,
            Booking.StatusChoices.CONFIRMED,
            Booking.StatusChoices.CHECKED_IN,
        ]

        selected_rooms = set()

        for form in self.forms:

            if not form.cleaned_data:
                continue

            if form.cleaned_data.get('DELETE', False):
                continue

            room = form.cleaned_data.get('room')

            if not room:
                continue

            # -----------------------------------------------------
            # Prevent selecting the same room twice
            # in the same booking
            # -----------------------------------------------------
            if room.id in selected_rooms:
                raise ValidationError(
                    f"Room {room.room_number} has been selected "
                    f"more than once for this booking."
                )

            selected_rooms.add(room.id)

            # -----------------------------------------------------
            # Check existing bookings
            # -----------------------------------------------------
            overlapping_bookings = BookingRoom.objects.filter(
                room=room,
                booking__status__in=active_statuses,
                booking__check_in__lt=check_out,
                booking__check_out__gt=check_in,
            )

            # If editing an existing booking, don't compare
            # against itself.
            if self.instance.pk:
                overlapping_bookings = overlapping_bookings.exclude(
                    booking=self.instance
                )

            if overlapping_bookings.exists():
                existing_booking = overlapping_bookings.first()

                raise ValidationError(
                    f"Room {room.room_number} is already booked "
                    f"from {existing_booking.booking.check_in} "
                    f"to {existing_booking.booking.check_out}. "
                    f"Please select another room."
                )
            
class BookingRoomInline(admin.TabularInline):
    model = BookingRoom
    formset = BookingRoomInlineFormSet
    extra = 1
    readonly_fields = ['subtotal_room', 'available_date']
    fields = ['room', 'number_of_nights', 'subtotal_room', 'available_date']


# =====================================================================
# 2. BOOKING ADMIN CONFIGURATION
# =====================================================================
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'hotel', 'check_in', 'check_out', 
        'status', 'subtotal', 'order_total', 'total', 'created_at'
    ]
    
    list_filter = ['status', 'booking_source', 'hotel', 'check_in', 'check_out']
    search_fields = ['id', 'user__username', 'user__email', 'hotel__name', 'special_request']
    readonly_fields = ['subtotal', 'order_total', 'discount', 'tax', 'total']
    
    fieldsets = (
        ('Core Details', {
            # FIXED: updated field name from 'number_of_guest' to 'number_of_guests'
            'fields': ('user', 'hotel', 'status', 'booking_source', 'number_of_guests')
        }),
        ('Stay Schedule', {
            'fields': (('check_in', 'check_in_status'), ('check_out', 'check_out_status'), 'special_request')
        }),
        ('Tax & Discount Adjustments', {
            'fields': (('discount_percentage', 'discount'), ('tax_percentage', 'tax'))
        }),
        ('Financial Breakdown Overview', {
            'classes': ('collapse',),
            'fields': ('subtotal', 'order_total', 'total')
        }),
    )

    inlines = [BookingRoomInline]

    def save_model(self, request, obj, form, change):
        """Triggers model-level clean methods safely during individual save sweeps."""
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Saves inline room objects and guarantees recalculation routines run
        atomically immediately following layout alterations.
        """
        with transaction.atomic():
            formset.save()
            # Force update calculated field parameters back to root record rows
            form.instance.update_subtotals(save=True)