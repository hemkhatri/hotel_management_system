# from decimal import Decimal
# from django.contrib import admin
# from django.db import transaction
# from django.db.models import Sum
# from .models import Order, OrderItem, Service, SubServiceItem


# # ==========================================
# # Inlines
# # ==========================================

# class SubServiceItemInline(admin.TabularInline):
#     """Allows adding and editing sub-items directly inside the parent Service."""
#     model = SubServiceItem
#     extra = 1
#     fields = ("name", "price", "is_available", "description")


# class OrderItemInline(admin.TabularInline):
#     """Allows staff to add items to an Order."""
#     model = OrderItem
#     extra = 1
#     # If using updated SubServiceItem schema, name field 'item' instead of 'service'
#     fields = ("item", "quantity", "unit_price", "subtotal")
#     readonly_fields = ("unit_price", "subtotal")


# # ==========================================
# # Model Admin Configurations
# # ==========================================

# @admin.register(Service)
# class ServiceAdmin(admin.ModelAdmin):
#     list_display = ("name", "hotel", "category", "custom_category_name", "items_count", "created_at")
#     list_filter = ("hotel", "category")
#     search_fields = ("name", "description", "custom_category_name", "hotel__name")
#     list_select_related = ("hotel",)
#     inlines = [SubServiceItemInline]

#     def get_queryset(self, request):
#         return super().get_queryset(request).annotate(
#             _items_count=Sum('items')
#         )

#     @admin.display(description="Total Sub-Items")
#     def items_count(self, obj):
#         return obj.items.count()


# @admin.register(SubServiceItem)
# class SubServiceItemAdmin(admin.ModelAdmin):
#     list_display = ("name", "service", "price", "is_available", "created_at")
#     list_filter = ("is_available", "service__hotel", "service__category")
#     search_fields = ("name", "description", "service__name")
#     list_select_related = ("service", "service__hotel")
#     list_editable = ("price", "is_available")


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ("id", "booking", "status", "subtotal", "created_at", "updated_at")
#     list_filter = ("status", "created_at")
#     search_fields = ("id", "booking__id", "booking__customer_id__username")
#     readonly_fields = ("subtotal", "created_at", "updated_at")
#     list_select_related = ("booking", "booking__customer_id")
#     list_editable = ("status",)
#     inlines = [OrderItemInline]

#     @transaction.atomic
#     def save_formset(self, request, form, formset, change):
#         """
#         Handles saving, deletion, price snapshots, and total recalculations atomically.
#         """
#         instances = formset.save(commit=False)

#         # 1. Handle deleted inline items first
#         for obj in formset.deleted_objects:
#             obj.delete()

#         # 2. Save new and modified items
#         for instance in instances:
#             if isinstance(instance, OrderItem):
#                 # Auto-populate price snapshot from SubServiceItem
#                 if not instance.unit_price and instance.item:
#                     instance.unit_price = instance.item.price

#                 instance.subtotal = (instance.unit_price * instance.quantity).quantize(Decimal('0.01'))
#                 instance.save()

#         formset.save_m2m()

#         # 3. Recalculate Order subtotal after deletions and additions are finalized
#         order = form.instance
#         if hasattr(order, 'update_subtotal'):
#             order.update_subtotal(save=True)
#         else:
#             order_items_total = order.items.aggregate(
#                 total=Sum('subtotal')
#             )['total'] or Decimal('0.00')
#             order.subtotal = order_items_total
#             order.save()

#         # 4. Trigger parent booking recalculation if implemented
#         if hasattr(order.booking, 'recalculate_totals'):
#             order.booking.recalculate_totals(save=True)
#         elif hasattr(order.booking, 'update_totals'):
#             order.booking.update_totals()


# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ("id", "order", "item", "quantity", "unit_price", "subtotal", "created_at")
#     list_filter = ("created_at",)
#     search_fields = ("order__id", "item__name")
#     list_select_related = ("order", "item")
#     readonly_fields = ("unit_price", "subtotal", "created_at")



# services/admin.py
from decimal import Decimal
from django import forms
from django.contrib import admin
from django.db import transaction

from .models import Service, SubServiceItem, Order, OrderItem


# ==========================================
# Service & SubService Admin
# ==========================================

class SubServiceItemInline(admin.TabularInline):
    model = SubServiceItem
    extra = 1
    fields = ("name", "price", "is_available", "description")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel", "category", "custom_category_name", "items_count", "created_at")
    list_filter = ("hotel", "category")
    search_fields = ("name", "description", "custom_category_name", "hotel__name")
    list_select_related = ("hotel",)
    inlines = [SubServiceItemInline]

    @admin.display(description="Total Items")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(SubServiceItem)
class SubServiceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price", "is_available", "created_at")
    list_filter = ("is_available", "service__hotel", "service__category")
    search_fields = ("name", "description", "service__name")
    list_select_related = ("service", "service__hotel")
    list_editable = ("price", "is_available")


# ==========================================
# Order & OrderItem Admin
# ==========================================

class OrderItemInlineForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "item" in self.fields:
            self.fields["item"].queryset = SubServiceItem.objects.filter(
                is_available=True
            ).select_related("service", "service__hotel")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemInlineForm
    extra = 1
    fields = ("item", "quantity", "unit_price", "subtotal")
    readonly_fields = ("unit_price", "subtotal")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "status", "subtotal", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "booking__id")
    readonly_fields = ("subtotal", "created_at", "updated_at")
    list_select_related = ("booking",)
    list_editable = ("status",)
    inlines = [OrderItemInline]

    @transaction.atomic
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        for instance in instances:
            if isinstance(instance, OrderItem):
                if not instance.unit_price and instance.item:
                    instance.unit_price = instance.item.price
                instance.subtotal = (instance.unit_price * instance.quantity).quantize(Decimal("0.01"))
                instance.save()

        formset.save_m2m()

        order = form.instance
        order.update_subtotal(save=True)