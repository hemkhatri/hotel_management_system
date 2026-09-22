from django.contrib import admin
from .models import Service, SubServiceItem, Order, OrderItem


# ==========================================
# 🛠️ SERVICE & SUB-SERVICE CONFIGURATION
# ==========================================


class SubServiceItemInline(admin.TabularInline):
    model = SubServiceItem
    extra = 1
    fields = ("name", "price", "is_available")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "custom_category_name",
        "hotel",
        "created_at",
    )
    list_filter = ("category", "hotel", "created_at")
    search_fields = ("name", "description", "custom_category_name", "hotel__name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Service Details", {"fields": ("hotel", "name", "description")}),
        ("Classification", {"fields": ("category", "custom_category_name")}),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )

    inlines = [SubServiceItemInline]


@admin.register(SubServiceItem)
class SubServiceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price", "is_available", "updated_at")
    list_filter = ("is_available", "service__category", "created_at")
    search_fields = ("name", "description", "service__name")
    readonly_fields = ("created_at", "updated_at")


# ==========================================
# 🛒 ORDER & ORDER ITEM CONFIGURATION
# ==========================================


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("service", "quantity", "unit_price", "subtotal")
    readonly_fields = ("subtotal", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "room_display",
        "user",
        "status",
        "total",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "booking__id",
        "room__room_number",
        "user__username",
        "user__email",
    )
    date_hierarchy = "created_at"

    fieldsets = (
        ("References", {"fields": ("booking", "room", "user")}),
        ("Order State & Billing", {"fields": ("status", "total")}),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )

    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline]

    @admin.display(description="Room")
    def room_display(self, obj):
        return f"Room {obj.room.room_number}"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "service",
        "quantity",
        "unit_price",
        "subtotal",
        "created_at",
    )
    list_filter = ("created_at", "service__category")
    search_fields = ("order__id", "service__name")
    readonly_fields = ("created_at", "subtotal")
