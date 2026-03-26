from rest_framework import serializers
from rentals.models import Tenancy


class TenancySerializer(serializers.ModelSerializer):
    # Flattening nested data so the frontend doesn't have to parse deep JSON objects
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    asset_name = serializers.CharField(source='unit.asset.name', read_only=True)

    class Meta:
        model = Tenancy
        fields = [
            'id', 'unit_name', 'asset_name', 'start_date', 'end_date',
            'status', 'rent_amount', 'next_payment_date', 'grace_period_days'
        ]