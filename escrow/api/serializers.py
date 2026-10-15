from rest_framework import serializers
from escrow.models import Escrow


class EscrowSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing Escrow transactions.
    Works for both the Tenant (sender) and the Landlord (recipient).
    """
    # 🟢 UPDATED: Direct paths using the new Workspace/Asset structure
    unit_name = serializers.CharField(source='tenancy.unit.name', read_only=True, default="General Escrow")
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    # 🟢 CHANGED: Replaced landlord_company with workspace_name
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)

    # 🟢 ADDED: Useful for frontend linking
    tenancy_id = serializers.IntegerField(source='tenancy.id', read_only=True)

    class Meta:
        model = Escrow
        fields = [
            'id',
            'workspace_id',
            'workspace_name',
            'tenancy_id',
            'unit_name',
            'tenant_name',
            'amount',
            'status',
            'start_date',
            'end_date',
            'created_at',
            'released_at'
        ]