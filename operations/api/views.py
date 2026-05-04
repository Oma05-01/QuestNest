# operations/api/views.py
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, filters, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView

from operations.models import Event, Task
from operations.api.serializers import EventSerializer, TaskSerializer, EventTraceSerializer
from operations.tasks import process_event_rules_task
from rest_framework.decorators import action
from rest_framework.response import Response

# 🟢 Only keep the ViewSets!
@method_decorator(csrf_exempt, name='dispatch')
class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'status', 'object_type', 'object_id']
    search_fields = ['event_type', 'object_id', 'metadata']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def retry(self, request, pk=None):
        """
        Allows an admin to manually re-trigger a failed event.
        POST /api/operations/events/{id}/retry/
        """
        event = self.get_object()

        # 1. Guardrail: Only allow retrying failed events
        if event.status != 'failed':
            return Response(
                {"detail": "Only failed events can be retried."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Cleanup: Wipe the old error tracebacks from the metadata
        metadata = event.metadata or {}
        keys_to_remove = [k for k in metadata.keys() if k.startswith('error_') or k.startswith('traceback_')]
        for k in keys_to_remove:
            metadata.pop(k, None)

        # 3. Reset: Mark it as pending again
        event.metadata = metadata
        event.status = 'pending'
        event.save(update_fields=['metadata', 'status'])

        # 4. Fire: Send it back to the Celery queue!
        process_event_rules_task.delay(event.id)

        return Response(
            {"detail": "Event has been successfully re-queued for processing."},
            status=status.HTTP_202_ACCEPTED
        )

    def get_queryset(self):
        user = self.request.user

        # 🟢 1. Global Admin Access: Superusers see the entire system ledger
        if user.is_superuser:
            return Event.objects.all().prefetch_related('rule_executions')

        # 🟢 2. Tenant Isolation: Regular users ONLY see their organisation's events
        if hasattr(user, 'organisation') and user.organisation is not None:
            return Event.objects.filter(
                organisation=user.organisation
            ).prefetch_related('rule_executions')

        # 🔴 3. The Safety Net: Default to denying access
        # If a user slips through without an org and isn't an admin, they see nothing.
        return Event.objects.none()

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'related_object_type', 'assigned_to']
    ordering_fields = ['created_at', 'due_date']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'organisation'):
            return Task.objects.filter(organisation=user.organisation)
        return Task.objects.none()


class EventTraceAPIView(APIView):
    """
    Returns a complete genealogy of an event:
    Rules executed + Child events triggered.
    """
    def get(self, request, pk):
        # We use select_related and prefetch_related to keep the DB hits low
        event = get_object_or_404(
            Event.objects.prefetch_related('rule_executions', 'child_events'),
            pk=pk
        )
        serializer = EventTraceSerializer(event)
        return Response(serializer.data)