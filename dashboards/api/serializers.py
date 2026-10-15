from rest_framework import serializers
from operations.models import Event
from rentals.models import Tenancy
from django.utils import timezone
from payments.models import Payment

class EventListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for populating dashboard activity tables.
    """
    # 🟢 CHANGED: organisation -> workspace
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    actor_email = serializers.CharField(source='actor.email', read_only=True, allow_null=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'event_type',
            'status',
            'workspace_name', # 🟢 CHANGED
            'actor_email',
            'created_at'
        ]


# 🟢 RENAMED: Replaced 'Landlord' with 'Workspace'
class WorkspaceTenancyListSerializer(serializers.ModelSerializer):
    # 🟢 CHANGED: Updated to use the new `tenant.name` field from the User model
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_email = serializers.CharField(source='tenant.email', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)

    # Calculate live status points
    is_overdue = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Tenancy
        fields = [
            'id', 'unit_name', 'tenant_name', 'tenant_email',
            'status', 'rent_amount', 'next_payment_date',
            'is_overdue', 'outstanding_balance'
        ]

    def get_is_overdue(self, obj):
        if obj.status != 'active' or not obj.next_payment_date:
            return False
        # Calculate if we've passed the due date + grace period
        grace_limit = obj.next_payment_date + timezone.timedelta(days=obj.grace_period_days)
        return timezone.now().date() > grace_limit

    def get_outstanding_balance(self, obj):
        # Uses the model method you likely already have
        if hasattr(obj, 'get_outstanding_balance'):
            return obj.get_outstanding_balance()
        return 0.00


# 🟢 RENAMED: This can now be used for BOTH Tenants and Property Managers!
class PaymentHistorySerializer(serializers.ModelSerializer):
    # Traverse the relationships to get the human-readable unit name
    unit_name = serializers.CharField(source='tenancy.unit.name', read_only=True, default="Unassigned")
    description = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'reference',
            'amount',
            'status',
            'created_at',
            'unit_name',
            'description'
        ]

    def get_description(self, obj):
        if obj.tenancy and obj.tenancy.unit:
            return f"Rent Payment - {obj.tenancy.unit.name}"
        return "General Payment"