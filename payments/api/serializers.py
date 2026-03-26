from rest_framework import serializers
from rentals.models import Tenancy


class PayRentSerializer(serializers.Serializer):
    tenancy_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        """
        Validate that the tenancy actually exists, is active, 
        and belongs to the person making the request.
        """
        user = self.context['request'].user
        try:
            tenancy = Tenancy.objects.get(
                id=data['tenancy_id'],
                tenant=user,
                status=Tenancy.ACTIVE
            )
            # Attach the tenancy object to the validated data so the view can pass it to the service
            data['tenancy'] = tenancy
        except Tenancy.DoesNotExist:
            raise serializers.ValidationError({
                "tenancy_id": "Active tenancy not found or does not belong to you."
            })

        if data['amount'] <= 0:
            raise serializers.ValidationError({"amount": "Payment amount must be greater than zero."})

        return data