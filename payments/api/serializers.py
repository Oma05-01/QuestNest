from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from payments.models import Payment
from rentals.models import Tenancy


class PayRentSerializer(serializers.Serializer):
    tenancy_id = serializers.PrimaryKeyRelatedField(
        queryset=Tenancy.objects.all(),
        source='tenancy'  # This maps 'tenancy_id' input to 'tenancy' in validated_data
    )
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    # payments/api/serializers.py

    def validate(self, data):
        """
        Validate that the tenancy belongs to the person making the request
        and is currently active.
        """
        user = self.context['request'].user
        # 🟢 Use 'tenancy' (the source/object), not 'tenancy_id'
        tenancy = data.get('tenancy')

        if not tenancy:
            raise serializers.ValidationError({"tenancy": "Tenancy not found."})

        # Since 'tenancy' is already an object, we just check its attributes
        if tenancy.tenant != user:
            raise serializers.ValidationError("You do not have permission to pay for this tenancy.")

        if tenancy.status != Tenancy.ACTIVE:
            raise serializers.ValidationError("This tenancy is not active.")

        recent_payment = Payment.objects.filter(
            user=user,
            tenancy=tenancy,
            amount=data['amount'],
            status='success',
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).exists()

        if recent_payment:
            raise serializers.ValidationError(
                "A successful payment for this tenancy was detected in the last 5 minutes. "
                "Please check your dashboard before trying again."
            )

        return data