from django.contrib import admin
from .models import Hotel, Amenity, RoomCategory

# =====================================================================
# 1. HOTEL ADMIN
# =====================================================================
@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'no_of_floor', 'email', 'updated_at']
    search_fields = ['name', 'address', 'email']
    list_filter = ['no_of_floor', 'created_at']


# =====================================================================
# 2. AMENITY ADMIN
# =====================================================================
@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'descripiton']
    search_fields = ['name', 'descripiton']


# =====================================================================
# 3. ROOM CATEGORY ADMIN
# =====================================================================
@admin.register(RoomCategory)
class RoomCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'max_occupancy', 'status', 'updated_at']
    list_filter = ['status', 'max_occupancy', 'created_at']
    search_fields = ['name', 'description']
    
    # Replaces the default multi-select box with a polished side-by-side selector
    filter_horizontal = ['amenities']
