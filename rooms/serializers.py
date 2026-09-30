from rest_framework import serializers

from .models import Room, RoomMedia


class RoomMediaSerializer(serializers.ModelSerializer):
    """Return a room's media metadata; successful output includes media type and caption."""

    class Meta:
        model = RoomMedia
        fields = ("id", "room", "media_type", "caption", "created_at")
        read_only_fields = ("id", "created_at")


class RoomSerializer(serializers.ModelSerializer):
    """Serialize rooms with category details and attached media for independent frontends."""

    category_detail = serializers.SerializerMethodField()
    media = RoomMediaSerializer(many=True, read_only=True, source="roommedia_set")

    class Meta:
        model = Room
        fields = ("id", "category", "category_detail", "room_number", "floor", "description", "status", "media", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_category_detail(self, obj):
        # The related category clarifies price and capacity in the successful room response.
        from hotels.serializers import RoomCategorySerializer
        return RoomCategorySerializer(obj.category, context=self.context).data
