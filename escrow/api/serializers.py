from rest_framework import serializers
from escrow.models import Escrow


class EscrowSerializer(serializers.ModelSerializer):
    # 🟢 FIX: Correctly path through the tenancy to get the unit
    unit_name = serializers.CharField(source='tenancy.unit.name', read_only=True, default="Unknown Unit")
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    # 🟢 FIX: Show the Organisation name, not the individual user who clicked the button
    landlord_company = serializers.CharField(source='tenancy.unit.asset.organisation.name', read_only=True)

    class Meta:
        model = Escrow
        fields = [
            'id', 'amount', 'status', 'start_date', 'end_date',
            'unit_name', 'tenant_name', 'landlord_company',
            'created_at', 'released_at'
        ]