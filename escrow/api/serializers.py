from rest_framework import serializers
from escrow.models import Escrow

class EscrowSerializer(serializers.ModelSerializer):
    # Flattening related fields for a cleaner frontend experience
    unit_name = serializers.CharField(source='unit.name', read_only=True, default="Unknown Unit")
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    landlord_name = serializers.CharField(source='landlord.name', read_only=True)

    class Meta:
        model = Escrow
        fields = [
            'id', 'amount', 'status', 'start_date', 'end_date', 
            'unit_name', 'tenant_name', 'landlord_name', 
            'created_at', 'released_at'
        ]