from rest_framework import permissions, viewsets

from .models import Amenity, Hotel, RoomCategory, RoomCategoryStatus
from .serializers import AmenitySerializer, HotelSerializer, RoomCategorySerializer


class StaffWriteReadOnly(permissions.BasePermission):
    """Allow public catalog reads and staff-only changes; denied writes return HTTP 403."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or bool(request.user and request.user.is_staff)


class HotelViewSet(viewsets.ModelViewSet):
    """List hotel records publicly and let staff create, edit, or remove them."""

    queryset = Hotel.objects.all().order_by("name")
    serializer_class = HotelSerializer
    permission_classes = (StaffWriteReadOnly,)

    def get_queryset(self):
        # Room categories are global in this schema, so the serializer handles that catalog separately.
        return super().get_queryset()


class AmenityViewSet(viewsets.ModelViewSet):
    """List amenities publicly and restrict catalog maintenance to staff accounts."""

    queryset = Amenity.objects.all().order_by("name")
    serializer_class = AmenitySerializer
    permission_classes = (StaffWriteReadOnly,)


class RoomCategoryViewSet(viewsets.ModelViewSet):
    """Manage room categories; public lists show active categories while staff can see all states."""

    serializer_class = RoomCategorySerializer
    permission_classes = (StaffWriteReadOnly,)

    def get_queryset(self):
        queryset = RoomCategory.objects.prefetch_related("amenities").order_by("name")
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(status=RoomCategoryStatus.ACTIVE)
        return queryset
