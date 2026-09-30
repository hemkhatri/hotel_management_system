from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Accept a payment attempt and expose its lifecycle; the client cannot claim settlement."""

    class Meta:
        model = Payment
        fields = ("id", "booking", "amount", "method", "status", "transaction_reference", "created_at", "updated_at")
        read_only_fields = ("id", "status", "transaction_reference", "created_at", "updated_at")
        extra_kwargs = {"amount": {"required": False}}

    def validate(self, attrs):
        # A guest may only pay for their own booking, and pending payment attempts cannot exceed its balance.
        booking = attrs["booking"]
        request = self.context.get("request")
        if request and not request.user.is_staff and booking.customer_id_id != request.user.pk:
            raise serializers.ValidationError({"booking": "You can only pay for your own booking."})
        already_paid = booking.payments.filter(status=Payment.StatusChoices.SUCCEEDED).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        pending = booking.payments.filter(status=Payment.StatusChoices.PENDING).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        amount = attrs.get("amount", booking.total)
        if amount <= Decimal("0.00"):
            raise serializers.ValidationError({"amount": "There is no outstanding amount to pay."})
        attrs["amount"] = amount
        if amount > max(Decimal("0.00"), booking.total - already_paid - pending):
            raise serializers.ValidationError({"amount": "Payment amount exceeds the outstanding booking balance."})
        if booking.status in ("CANCELLED", "EXPIRED"):
            raise serializers.ValidationError({"booking": "This booking cannot receive payments."})
        return attrs
