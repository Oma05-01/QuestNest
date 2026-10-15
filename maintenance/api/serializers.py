from rest_framework import serializers
from maintenance.models import MaintenanceRequest, MaintenanceImage, Vendor, MaintenanceAssignment, MaintenanceComment


class MaintenanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceImage
        fields = ['id', 'image', 'uploaded_at']


class MaintenanceSerializer(serializers.ModelSerializer):
    # 🟢 Identity & Context
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    property_name = serializers.CharField(source='unit.asset.name', read_only=True)
    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)

    images = MaintenanceImageSerializer(many=True, read_only=True)

    # Choice labels for a prettier UI
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'workspace_id', 'title', 'description', 'priority', 'priority_display',
            'status', 'status_display', 'unit', 'unit_name', 'property_name',
            'tenant', 'tenant_name', 'estimated_cost', 'created_at', 'updated_at', 'images'
        ]
        # 🟢 CHANGED: Replaced organisation with workspace
        read_only_fields = ['workspace', 'tenant', 'status']


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'category', 'phone', 'email']


class MaintenanceAssignmentSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    request_title = serializers.CharField(source='request.title', read_only=True)
    unit_name = serializers.CharField(source='request.unit.name', read_only=True)
    property_name = serializers.CharField(source='request.unit.asset.name', read_only=True)

    class Meta:
        model = MaintenanceAssignment
        fields = [
            'id', 'request_title', 'unit_name', 'property_name',
            'vendor', 'vendor_name', 'assigned_at', 'notes', 'cost'
        ]


class MaintenanceCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceComment
        fields = ['id', 'author_name', 'body', 'created_at', 'is_me']

    def get_is_me(self, obj):
        request = self.context.get('request')
        return request.user == obj.author if request else False