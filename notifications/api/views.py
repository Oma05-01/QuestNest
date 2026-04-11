from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.api.permissions import BelongsToOrganisation
from notifications.models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Users can view their notifications and mark them as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [BelongsToOrganisation]

    def get_queryset(self):
        # 🛡️ Only show notifications for the logged-in user
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})