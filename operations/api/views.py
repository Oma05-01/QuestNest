from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.api.permissions import IsAdmin
from operations.models import Event, Task
from .serializers import EventSerializer, TaskSerializer


class EventListView(APIView):
    """ GET /api/events/ """
    # Strictly Admins only! This is your system's raw ledger.
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        # We limit to 100 to prevent the database from choking on massive event logs.
        # You can add proper DRF pagination later when the frontend needs it.
        events = Event.objects.all().select_related('actor').order_by('-created_at')[:100]
        return Response(EventSerializer(events, many=True).data)


class TaskListView(APIView):
    """ GET /api/tasks/ """
    # Any authenticated user can hit this, but the view filters the data
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin':
            # Admins see the global task queue
            tasks = Task.objects.all().order_by('due_date')[:50]
        else:
            # Tenants, Landlords, and Staff only see tasks assigned to them personally
            tasks = Task.objects.filter(assigned_to=request.user).order_by('due_date')

        return Response(TaskSerializer(tasks, many=True).data)