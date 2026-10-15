from rest_framework import serializers
from notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    # 🟢 ADDED: Workspace context
    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'workspace_id', 'title', 'message',
            'notification_type', 'is_read', 'created_at', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'workspace_id']