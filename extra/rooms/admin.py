from django.contrib import admin
from .models import Room, RoomMedia

# =====================================================================
# 1. ROOM MEDIA INLINE INTERFACE
# =====================================================================
class RoomMediaInline(admin.TabularInline):
    model = RoomMedia
    extra = 1
    fields = ['media_type', 'caption']
    # You might want to add 'media_file' here later when you integrate File/Image fields.


# =====================================================================
# 2. ROOM ADMIN CONFIGURATION
# =====================================================================
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    # Columns shown in the rooms table view
    list_display = ['room_number', 'hotel', 'category', 'floor', 'status', 'updated_at']
    
    # Sidebar filtration elements
    list_filter = ['status', 'hotel', 'category', 'floor']
    
    # Global search index bars
    search_fields = ['room_number', 'description', 'hotel__name', 'category__name']
    
    # Embed media files directly under the room form
    inlines = [RoomMediaInline]

    def save_model(self, request, obj, form, change):
        """
        Forces Django Admin to execute model clean constraints, 
        ensuring room floor calculations match hotel total floor restrictions.
        """
        obj.full_clean()
        super().save_model(request, obj, form, change)


# =====================================================================
# 3. STANDALONE ROOM MEDIA VIEW (OPTIONAL)
# =====================================================================
@admin.register(RoomMedia)
class RoomMediaAdmin(admin.ModelAdmin):
    list_display = ['room', 'media_type', 'caption', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['room__room_number', 'caption']
