from rest_framework import decorators, permissions, response, status, viewsets

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """Create pending payment attempts and let staff record settlement outcomes."""

    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        # Guests see only their own payments; staff can reconcile all payment records.
        queryset = Payment.objects.select_related("booking", "booking__customer_id").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(booking__customer_id=self.request.user)

    def perform_create(self, serializer):
        # Only create a pending attempt; no card processor is configured in this project.
        serializer.save(processed_by=self.request.user if self.request.user.is_staff else None)

    @decorators.action(detail=True, methods=("post",), permission_classes=(permissions.IsAdminUser,))
    def settle(self, request, pk=None):
        """Record a staff-confirmed outcome; HTTP 200 means reconciliation was saved successfully."""
        payment = self.get_object()
        outcome = request.data.get("status")
        allowed = {Payment.StatusChoices.SUCCEEDED, Payment.StatusChoices.FAILED, Payment.StatusChoices.REFUNDED}
        if outcome not in allowed:
            return response.Response({"status": [f"Choose one of: {', '.join(sorted(allowed))}."]}, status=400)
        payment.status = outcome
        payment.transaction_reference = request.data.get("transaction_reference", payment.transaction_reference)
        payment.processed_by = request.user
        payment.save(update_fields=("status", "transaction_reference", "processed_by", "updated_at"))
        return response.Response(self.get_serializer(payment).data, status=status.HTTP_200_OK)
