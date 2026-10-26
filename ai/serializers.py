# ai/serializers.py
from rest_framework import serializers

class MaintenanceTriageRequestSerializer(serializers.Serializer):
    description = serializers.CharField(
        required=True,
        min_length=10,
        help_text="Raw, unstructured maintenance complaint from the tenant."
    )
    # 🟢 CHANGED: Use IntegerField to match the Unit model's primary key
    unit_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Target unit ID. If omitted, resolves from tenant's active tenancy."
    )