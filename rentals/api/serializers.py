from rest_framework import serializers
from rentals.models import Tenancy
from accounts.models import User


class TenancySerializer(serializers.ModelSerializer):
    # 🟢 ADDED: Contextual info for the dashboard
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    asset_name = serializers.CharField(source='unit.asset.name', read_only=True)

    # 🟢 ADDED: Tenant details (Essential for the Property Manager's view)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_email = serializers.CharField(source='tenant.email', read_only=True)

    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)

    class Meta:
        model = Tenancy
        fields = [
            'id', 'workspace_id', 'unit_name', 'asset_name',
            'tenant_name', 'tenant_email', 'start_date', 'end_date',
            'status', 'rent_amount', 'deposit_amount',
            'next_payment_date', 'grace_period_days'
        ]


class CreateTenancySerializer(serializers.ModelSerializer):
    """
    Used by Property Managers to draft a new lease.
    The 'tenant' field expects a User ID.
    """

    class Meta:
        model = Tenancy
        fields = [
            'unit', 'tenant', 'start_date', 'end_date',
            'rent_amount', 'deposit_amount', 'grace_period_days'
        ]

    def validate_unit(self, value):
        # 🟢 SAFETY CHECK: Ensure the unit belongs to the active workspace
        request = self.context.get('request')
        if value.workspace != request.workspace:
            raise serializers.ValidationError("This unit does not belong to your workspace.")
        return value