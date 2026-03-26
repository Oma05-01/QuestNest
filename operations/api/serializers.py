from rest_framework import serializers
from operations.models import Event, Task

class EventSerializer(serializers.ModelSerializer):
    # Pull the email so the frontend doesn't just get a user ID
    actor_email = serializers.CharField(source='actor.email', read_only=True, default="System")

    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'object_type', 'object_id', 
            'status', 'actor_email', 'metadata', 'created_at'
        ]

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'due_date', 
            'related_object_type', 'related_object_id', 'created_at'
        ]