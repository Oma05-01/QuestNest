from rest_framework import serializers
from leases.models import LeaseAgreement, LeaseClauseInstance, LeaseSignature
from rentals.models import Tenancy
from escrow.models import Escrow


class LeaseClauseInstanceSerializer(serializers.ModelSerializer):
    # template.title comes from the LeaseTemplate linked to the instance
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
    tenant_name = serializers.CharField(source='tenancy.tenant.name', read_only=True)
    clauses = LeaseClauseInstanceSerializer(many=True, read_only=True)
    signatures = LeaseSignatureSerializer(many=True, read_only=True)

    # 🟢 ADDED: Workspace context
    workspace_id = serializers.UUIDField(source='tenancy.workspace.id', read_only=True)

    escrow_id = serializers.SerializerMethodField()
    escrow_status = serializers.SerializerMethodField()

    class Meta:
        model = LeaseAgreement
        fields = [
            'id', 'workspace_id', 'unit_name', 'tenant_name', 'rent_amount', 'deposit_amount',
            'start_date', 'end_date', 'status', 'clauses', 'signatures',
            'escrow_id', 'escrow_status'
        ]

    def get_escrow_id(self, obj):
        # We look for the escrow linked to the underlying tenancy
        escrow = Escrow.objects.filter(tenancy=obj.tenancy).first()
        return escrow.id if escrow else None

    def get_escrow_status(self, obj):
        escrow = Escrow.objects.filter(tenancy=obj.tenancy).first()
        return escrow.status if escrow else None


class CreateLeaseSerializer(serializers.Serializer):
    tenancy_id = serializers.UUIDField()

    def validate_tenancy_id(self, value):
        request = self.context.get('request')
        try:
            # 🟢 OPTIMIZED: Direct workspace check using the new Tenancy model structure
            tenancy = Tenancy.objects.select_related('workspace').get(id=value)

            # 🛡️ SECURITY: Only a manager in the CORRECT workspace can generate a lease
            if tenancy.workspace != request.workspace:
                raise serializers.ValidationError(
                    "You do not have permission to generate a lease for a tenancy outside your active workspace."
                )

            return tenancy
        except Tenancy.DoesNotExist:
            raise serializers.ValidationError("Tenancy record not found.")