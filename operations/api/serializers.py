from rest_framework import serializers
from operations.models import Event, Task, RuleExecution

class RuleExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleExecution
        fields = ['id', 'rule_name', 'executed_at', 'status', 'error_message', 'execution_time']
        read_only_fields = ['id', 'rule_name', 'executed_at', 'status', 'error_message', 'execution_time']

class EventSerializer(serializers.ModelSerializer):
    # Pull the email so the frontend doesn't just get a user ID
    actor_email = serializers.CharField(source='actor.email', read_only=True, default="System")
    executions = RuleExecutionSerializer(source='ruleexecution_set', many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'object_type', 'object_id', 
            'status', 'workspace', 'metadata', 'created_at', 'executions', 'actor_email', # 🟢 CHANGED: organisation -> workspace
        ]

        read_only_fields = [
            'id',
            'workspace', # 🟢 CHANGED
            'actor',
            'event_type',
            'object_type',
            'object_id',
            'created_at'
        ]


class EventTraceSerializer(serializers.ModelSerializer):
    # Get the rule results for this specific event
    executions = RuleExecutionSerializer(source='rule_executions', many=True, read_only=True)

    # Recursively get child events (The 'Genealogy')
    children = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'status', 'object_type',
            'object_id', 'metadata', 'created_at',
            'executions', 'children'
        ]

    def get_children(self, obj):
        # We only go one level deep here to prevent massive response sizes,
        # but the client can follow the IDs down the rabbit hole.
        children = obj.child_events.all()
        return EventTraceSerializer(children, many=True).data


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'due_date',
            'related_object_type', 'related_object_id', 'created_at'
        ]

        read_only_fields = [
            'id',
            'workspace', # 🟢 CHANGED: organisation -> workspace
            'related_object_type',
            'related_object_id',
            'created_at'
        ]