from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, filters, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response

from operations.models import Event, Task
from operations.api.serializers import EventSerializer, TaskSerializer, EventTraceSerializer
from operations.tasks import process_event_rules_task

# 🟢 ADDED: Import our custom context-aware permission
from core.api.permissions import IsWorkspaceMember


@method_decorator(csrf_exempt, name='dispatch')
class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    # 🟢 CHANGED: Enforce workspace membership globally for this ViewSet
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'status', 'object_type', 'object_id']
    search_fields = ['event_type', 'object_id', 'metadata']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsWorkspaceMember])
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

        # 1. Global Admin Access: Superusers see the entire system ledger
        # (Assuming they aren't explicitly browsing within a workspace context)
        if user.is_superuser and not getattr(self.request, 'workspace', None):
            return Event.objects.all().prefetch_related('rule_executions')

        # 🟢 2. Context Isolation: Regular users ONLY see events for their active workspace
        if getattr(self.request, 'workspace', None):
            return Event.objects.filter(
                workspace=self.request.workspace
            ).prefetch_related('rule_executions')

        # 🔴 3. The Safety Net: Default to denying access
        return Event.objects.none()


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    # 🟢 CHANGED: Enforce workspace membership
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'related_object_type', 'assigned_to']
    ordering_fields = ['created_at', 'due_date']
    ordering = ['-created_at']

    def get_queryset(self):
        # 🟢 CHANGED: Filter strictly by active workspace context
        if getattr(self.request, 'workspace', None):
            return Task.objects.filter(workspace=self.request.workspace)
        return Task.objects.none()


class EventTraceAPIView(APIView):
    """
    Returns a complete genealogy of an event:
    Rules executed + Child events triggered.
    """
    # 🟢 CHANGED: Secure this endpoint
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request, pk):
        # 🛡️ SECURITY FIX: Ensure the event being traced actually belongs to the active workspace!
        # Previously, anyone with a valid UUID could trace another company's events.
        event = get_object_or_404(
            Event.objects.prefetch_related('rule_executions', 'child_events'),
            pk=pk,
            workspace=request.workspace
        )
        serializer = EventTraceSerializer(event)
        return Response(serializer.data)