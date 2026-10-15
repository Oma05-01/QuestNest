from operations.models import Event
from operations.tasks import process_event_rules_task

def log_event(
    *,
    workspace, # 🟢 CHANGED: Replaced organisation
    actor=None,
    event_type,
    object_type=None,
    object_id=None,
    metadata=None,
    parent_event=None,
):
    """
    Logs an event and passes it to the background worker to evaluate rules.
    """
    # 1️⃣ Create the event (Fast)
    event = Event.objects.create(
        workspace=workspace, # 🟢 CHANGED
        actor=actor,
        event_type=event_type,
        object_type=object_type,
        object_id=object_id,
        metadata=metadata or {},
        parent_event=parent_event
    )

    # 2️⃣ Hand off to Celery / Memurai (Instant)
    process_event_rules_task.delay(event.id)

    return event