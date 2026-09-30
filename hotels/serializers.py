from rest_framework import serializers

from .models import Amenity, Hotel, RoomCategory


class AmenitySerializer(serializers.ModelSerializer):
    """Serialize one amenity; a successful response contains its stable ID and display name."""

    class Meta:
        model = Amenity
        fields = ("id", "name")


class RoomCategorySerializer(serializers.ModelSerializer):
    """Expose room-category pricing, capacity, amenities, and publication status."""

    amenities_detail = AmenitySerializer(source="amenities", many=True, read_only=True)

    class Meta:
        model = RoomCategory
        fields = ("id", "name", "description", "base_price", "max_occupancy", "amenities", "amenities_detail", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class HotelSerializer(serializers.ModelSerializer):
    """Expose hotel details; room categories are served separately because the schema has no hotel link."""

    class Meta:
        model = Hotel
        fields = ("id", "name", "address", "phone", "email", "description", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
