from decimal import Decimal
from django.contrib import admin
from django.db.models import Sum
from .models import Order, OrderItem, Service, SubServiceItem


# ==========================================
# Inlines
# ==========================================

class SubServiceItemInline(admin.TabularInline):
    """Allows adding and editing menu/sub-items directly inside the parent Service."""
    model = SubServiceItem
    extra = 1
    fields = ("name", "price", "is_available", "description")


class OrderItemInline(admin.TabularInline):
    """Allows staff to add services/items to an Order."""
    model = OrderItem
    extra = 1
    fields = ("service", "quantity", "unit_price", "subtotal")
    readonly_fields = ("subtotal",)


# ==========================================
# Model Admin Configurations
# ==========================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel", "category", "custom_category_name", "items_count", "created_at")
    list_filter = ("hotel", "category")
    search_fields = ("name", "description", "custom_category_name", "hotel__name")
    inlines = [SubServiceItemInline]

    @admin.display(description="Total Sub-Items")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(SubServiceItem)
class SubServiceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price", "is_available", "created_at")
    list_filter = ("is_available", "service__hotel", "service__category")
    search_fields = ("name", "description", "service__name")
    list_editable = ("price", "is_available")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "status", "subtotal", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "booking__id", "booking__user__username")
    readonly_fields = ("subtotal", "created_at", "updated_at")
    list_editable = ("status",)
    inlines = [OrderItemInline]

    def save_formset(self, request, form, formset, change):
        """
        Automatically updates unit_price, line item subtotal, 
        and order total whenever items are added/edited in Admin.
        """
        instances = formset.save(commit=False)
        
        for instance in instances:
            if isinstance(instance, OrderItem):
                # Auto-populate unit price from SubServiceItem if available, or keep existing unit_price
                if not instance.unit_price and hasattr(instance, 'service'):
                    # Fallback default if needed
                    instance.unit_price = getattr(instance.service, 'price', Decimal('0.00'))
                
                # Calculate OrderItem subtotal
                instance.subtotal = instance.unit_price * instance.quantity
                instance.save()

        formset.save_m2m()

        # Recalculate Order subtotal from non-deleted items
        order = form.instance
        order_items_total = order.items.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')

        order.subtotal = order_items_total
        order.save()

        # Trigger parent booking recalculation if update_totals is defined
        if hasattr(order.booking, 'update_totals'):
            order.booking.update_totals()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "service", "quantity", "unit_price", "subtotal", "created_at")
    list_filter = ("created_at",)
    search_fields = ("order__id", "service__name")
    readonly_fields = ("subtotal", "created_at")