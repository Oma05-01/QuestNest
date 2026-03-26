from rest_framework import serializers
from leases.models import LeaseAgreement, LeaseClauseInstance, LeaseSignature
from rentals.models import Tenancy


class LeaseClauseInstanceSerializer(serializers.ModelSerializer):
    # Pull the title from the template if you want it displayed as a header
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
    # Nest the clauses and signatures so the frontend can render the whole document
    clauses = LeaseClauseInstanceSerializer(many=True, read_only=True)
    signatures = LeaseSignatureSerializer(many=True, read_only=True)

    class Meta:
        model = LeaseAgreement
        fields = [
            'id', 'unit_name', 'rent_amount', 'deposit_amount',
            'start_date', 'end_date', 'status', 'clauses', 'signatures'
        ]


class CreateLeaseSerializer(serializers.Serializer):
    """
    Because your service extracts all the data from the Tenancy,
    the frontend only needs to pass the tenancy ID!
    """
    tenancy_id = serializers.UUIDField()

    def validate_tenancy_id(self, value):
        user = self.context['request'].user
        try:
            # We fetch the tenancy and ensure the person creating the lease 
            # actually owns the property (or is an admin)
            tenancy = Tenancy.objects.select_related('unit__asset').get(id=value)

            if user.role == 'landlord' and tenancy.unit.asset.owner != user:
                raise serializers.ValidationError("You do not own this property.")

            return tenancy
        except Tenancy.DoesNotExist:
            raise serializers.ValidationError("Tenancy not found.")