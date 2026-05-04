from rest_framework import serializers
from leases.models import LeaseAgreement, LeaseClauseInstance, LeaseSignature
from rentals.models import Tenancy

class LeaseClauseInstanceSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='template.title', read_only=True)

    class Meta:
        model = LeaseClauseInstance
        fields = ['id', 'title', 'body', 'order']


class LeaseSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseSignature
        fields = ['id', 'role', 'signed_name', 'signed_at']


class LeaseSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='tenancy.unit.name', read_only=True)
    tenant_name = serializers.CharField(source='tenancy.tenant.name', read_only=True) # Good to have for UI
    clauses = LeaseClauseInstanceSerializer(many=True, read_only=True)
    signatures = LeaseSignatureSerializer(many=True, read_only=True)
    escrow_id = serializers.SerializerMethodField()
    escrow_status = serializers.SerializerMethodField()

    class Meta:
        model = LeaseAgreement
        fields = [
            'id', 'unit_name', 'tenant_name', 'rent_amount', 'deposit_amount',
            'start_date', 'end_date', 'status', 'clauses', 'signatures',
            'escrow_id', 'escrow_status'
        ]

    def get_escrow_id(self, obj):
        # Find the escrow linked to this tenancy
        from escrow.models import Escrow
        escrow = Escrow.objects.filter(tenancy=obj.tenancy).first()
        return escrow.id if escrow else None

    def get_escrow_status(self, obj):
        from escrow.models import Escrow
        escrow = Escrow.objects.filter(tenancy=obj.tenancy).first()
        return escrow.status if escrow else None


class CreateLeaseSerializer(serializers.Serializer):
    tenancy_id = serializers.UUIDField()

    def validate_tenancy_id(self, value):
        user = self.context['request'].user
        try:
            tenancy = Tenancy.objects.select_related('unit__asset__organisation').get(id=value)

            # 🟢 FIX: Check the Organisation, not the Owner!
            if user.role in ['landlord', 'admin'] and tenancy.unit.asset.organisation != user.organisation:
                raise serializers.ValidationError("You do not have permission to generate a lease for this property.")

            return tenancy
        except Tenancy.DoesNotExist:
            raise serializers.ValidationError("Tenancy not found.")