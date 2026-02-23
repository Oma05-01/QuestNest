from operations.rules import register_rule
from operations.constants import EventType
from operations.models import Task
from operations.services.event_service import log_event


@register_rule(trigger_event=EventType.PAYMENT_STATUS_CHANGED)
def create_task_on_successful_payment(event):

    if event.metadata.get("to") != "success":
        return

    organisation = event.organisation

    task = Task.objects.create(
        organisation=organisation,
        title="Confirm receipt of payment",
        related_object_type="Payment",
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
