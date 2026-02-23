from operations.models import Event, EventRule
from operations.services.task_service import create_task
from django.db.models import Q
from operations.constants import EventType

def log_event(
    *,
    organisation,
    actor=None,
    event_type,
    object_type=None,
    object_id=None,
    metadata=None,
    parent_event=None,
):
    """
    Logs an event and executes any rules associated with it.
    """
    # 1️⃣ Create the event
    event = Event.objects.create(
        organisation=organisation,
        actor=actor,
        event_type=event_type,
        object_type=object_type,
        object_id=object_id,
        metadata=metadata or {},
        parent_event=parent_event
    )

    # 2️⃣ Fetch active rules (global + org-specific)
    rules = EventRule.objects.filter(
        event_type=event_type,
        is_active=True
    ).filter(
        Q(organisation=organisation) | Q(organisation__isnull=True)
    ).order_by("execution_order")

    # 3️⃣ Execute rules
    for rule in rules:
        if rule.action_type == "CREATE_TASK":
            task = create_task(
                organisation=organisation,
                title=rule.task_title,
                description=rule.task_description,
                related_object_type=object_type,
                related_object_id=object_id
            )

            # Log child event
            log_event(
                organisation=organisation,
                actor=None,  # system-triggered
                event_type=EventType.TASK_CREATED,
                object_type="Task",
                object_id=str(task.id),
                metadata={
                    "triggered_by_event": event.event_type
                },
                parent_event=event
            )

    return event
