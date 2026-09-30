from django.urls import include, path
from rest_framework import routers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.api import LoginView, LogoutView, MeView, RegisterView
from bookings.api import BookingRoomViewSet, BookingViewSet
from hotels.api import AmenityViewSet, HotelViewSet, RoomCategoryViewSet
from payments.api import PaymentViewSet
from rooms.api import RoomMediaViewSet, RoomViewSet
from services.api import OrderItemViewSet, OrderViewSet, ServiceViewSet, SubServiceItemViewSet


router = routers.DefaultRouter()
router.register("hotels", HotelViewSet, basename="hotel")
router.register("amenities", AmenityViewSet, basename="amenity")
router.register("room-categories", RoomCategoryViewSet, basename="room-category")
router.register("rooms", RoomViewSet, basename="room")
router.register("room-media", RoomMediaViewSet, basename="room-media")
router.register("bookings", BookingViewSet, basename="booking")
router.register("booking-rooms", BookingRoomViewSet, basename="booking-room")
router.register("services", ServiceViewSet, basename="service")
router.register("service-items", SubServiceItemViewSet, basename="service-item")
router.register("orders", OrderViewSet, basename="order")
router.register("order-items", OrderItemViewSet, basename="order-item")
router.register("payments", PaymentViewSet, basename="payment")


@api_view(("GET",))
@permission_classes((AllowAny,))
def health(request):
    """Report that the API process is responding; HTTP 200 with ok=true means it is reachable."""
    return Response({"ok": True, "api_version": "v1"})


urlpatterns = [
    path("health/", health, name="api-health"),
    path("auth/register/", RegisterView.as_view(), name="api-register"),
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/logout/", LogoutView.as_view(), name="api-logout"),
    path("auth/me/", MeView.as_view(), name="api-me"),
    path("", include(router.urls)),
]
