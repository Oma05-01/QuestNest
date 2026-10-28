# ai/serializers.py
from rest_framework import serializers
from django.core.validators import FileExtensionValidator

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

class LeaseDocumentUploadSerializer(serializers.Serializer):
    tenancy_id = serializers.IntegerField(
        required=True,
        help_text="ID of the tenancy this lease belongs to."
    )
    file = serializers.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="The lease document (PDF only)."
    )

class LeaseQuerySerializer(serializers.Serializer):
    tenancy_id = serializers.IntegerField(
        help_text="ID of the tenancy whose lease is being queried."
    )
    query = serializers.CharField(
        max_length=1000,
        help_text="The question to ask about the lease agreement."
    )