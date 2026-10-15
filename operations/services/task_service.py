from operations.models import Task
from operations.constants import EventType

def create_task(
    *,
    workspace,          # 🟢 CHANGED: Replaced organisation
    title,
    description="",
    assigned_to=None,
    related_object_type=None,
    related_object_id=None,
    due_date=None,
    parent_event=None,
    actor=None
):
    # 1. Create the task
    task = Task.objects.create(
        workspace=workspace,  # 🟢 CHANGED
        title=title,
        description=description,
        assigned_to=assigned_to,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        due_date=due_date
    )

    # Note: Import locally to avoid circular imports if event_service imports task_service
    from operations.services.event_service import log_event

    # 2. Automatically log the event
    log_event(
        workspace=workspace,  # 🟢 CHANGED
        actor=actor,
        event_type=EventType.TASK_CREATED,
        object_type="Task",
        object_id=str(task.id),
        metadata={
            "title": task.title,
            "related_to": related_object_type
        },
        parent_event=parent_event
    )

    return task