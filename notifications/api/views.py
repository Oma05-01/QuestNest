from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# 🟢 NEW: Context-aware permission
from core.api.permissions import IsWorkspaceMember
from notifications.models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Users can view their notifications for the ACTIVE workspace
    and mark them as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get_queryset(self):
        # 🛡️ ONLY show notifications for this specific User within the ACTIVE Workspace
        # This keeps the Personal and Business alerts strictly separated.
        return Notification.objects.filter(
            user=self.request.user,
            workspace=self.request.workspace
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        # get_object() automatically respects the get_queryset() filter above
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        # Bulk update only the notifications for the current workspace context
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})