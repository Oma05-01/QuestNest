from rest_framework import serializers
from operations.models import Event, Task, RuleExecution

class RuleExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleExecution
        fields = ['id', 'rule_name', 'executed_at']
        read_only_fields = ['id', 'rule_name', 'executed_at']

class EventSerializer(serializers.ModelSerializer):
    # Pull the email so the frontend doesn't just get a user ID
    actor_email = serializers.CharField(source='actor.email', read_only=True, default="System")
    executions = RuleExecutionSerializer(source='ruleexecution_set', many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'object_type', 'object_id', 
            'status', 'organisation', 'metadata', 'created_at', 'executions', 'actor_email',
        ]

        read_only_fields = [
            'id',
            'organisation',
            'actor',
            'event_type',
            'object_type',
            'object_id',
            'created_at'
            # Note: We leave 'status' and 'metadata' out of read_only_fields ONLY IF
            # you plan to build a "Retry Failed Event" endpoint later. Otherwise, add them here!
        ]

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'due_date', 
            'related_object_type', 'related_object_id', 'created_at'
        ]

        read_only_fields = [
            'id',
            'organisation',
            'related_object_type',
            'related_object_id',
            'created_at'
        ]