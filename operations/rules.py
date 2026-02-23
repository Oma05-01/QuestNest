from operations.models import Task
from operations.constants import EventType
from operations.services.event_service import log_event
from collections import defaultdict

# ------------------------
# Rule Registry
# ------------------------
_RULES_REGISTRY = defaultdict(list)

def register_rule(trigger_event):
    """
    Decorator to register a function as a rule for a specific event type.
    """
    def decorator(func):
        _RULES_REGISTRY[trigger_event].append(func)
        return func
    return decorator

def execute_rules(event):
    """
    Execute all rules registered for this event type.
    """
    organisation = event.organisation

    # Execute any rules registered via @register_rule
    for rule_func in _RULES_REGISTRY.get(event.event_type, []):
        rule_func(event)

    # ------------------------
    # Existing hard-coded task logic
    # ------------------------
    if event.event_type == EventType.PROPERTY_STATUS_CHANGED:
        if event.metadata.get("to") == "reserved":
            task = Task.objects.create(
                organisation=organisation,
                title="Prepare tenancy agreement",
                related_object_type="Property",
                related_object_id=event.object_id,
                created_by=None
            )

            log_event(
                organisation=organisation,
                actor=None,
                event_type=EventType.TASK_CREATED,
                object_type="Task",
                object_id=str(task.id),
                metadata={
                    "triggered_by_event": event.event_type
                },
                parent_event=event
            )
