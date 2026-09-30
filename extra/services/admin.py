from django.contrib import admin
from django.db import transaction
from .models import Service, SubServicesItem, Order, OrderItem

# =====================================================================
# 1. SERVICE & SUB-SERVICES INLINE
# =====================================================================
class SubServicesItemInline(admin.TabularInline):
    model = SubServicesItem
    extra = 1
    fields = ['name', 'price', 'is_avilable']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel', 'category', 'custom_category_name', 'created_at']
    list_filter = ['category', 'hotel']
    search_fields = ['name', 'description', 'custom_category_name']
    inlines = [SubServicesItemInline]

    # Guarantees full model clean validation handles custom_category rules in admin
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# =====================================================================
# 2. ORDER & ORDER ITEMS INLINE
# =====================================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    # unit_price and subtotal are auto-calculated, so make them read-only in admin
    readonly_fields = ['unit_price', 'subtotal']
    fields = ['item', 'quantity', 'unit_price', 'subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'status', 'subtotal', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'booking__id', 'booking__customer__username'] 
    readonly_fields = ['subtotal']
    inlines = [OrderItemInline]

    def save_formset(self, request, form, formset, change):
        """
        Calculates and pushes order subtotals upwards after an admin updates 
        individual items in the panel grid.
        """
        with transaction.atomic():
            # Save the items (this fires OrderItem.save() which updates prices/subtotals)
            formset.save()
            # Force the parent order instance to run aggregation & update tracking tables
            form.instance.update_subtotal(save=True)

    def delete_model(self, request, obj):
        """Ensures underlying booking financials update if an admin drops an order."""
        booking = obj.booking
        super().delete_model(request, obj)
        if hasattr(booking, 'update_subtotals'):
            booking.update_subtotals(save=True)
