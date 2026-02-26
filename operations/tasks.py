from celery import shared_task
from django.db.models import Q
from operations.models import Event, EventRule
from operations.services.task_service import create_task
from operations.constants import EventType


@shared_task
def process_event_rules_task(event_id):
    """
    Background worker that fetches dynamic EventRules from the DB and executes them.
    """
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    # Fetch active rules (global + org-specific)
    rules = EventRule.objects.filter(
        event_type=event.event_type,
        is_active=True
    ).filter(
        Q(organisation=event.organisation) | Q(organisation__isnull=True)
    ).order_by("execution_order")

    for rule in rules:
        if rule.action_type == "CREATE_TASK":
            # This now creates the task AND fires the child event automatically!
            create_task(
                organisation=event.organisation,
                title=rule.task_title,
                description=rule.task_description,
                related_object_type=event.object_type,
                related_object_id=event.object_id,
                parent_event=event  # Pass the trigger event to link them
            )

            # Note: We must import log_event locally inside the task
            # to avoid a circular import error with services.py
            from operations.services.event_service import log_event

            # Log child event (This safely queues another background task!)
            log_event(
                organisation=event.organisation,
                actor=None,
                event_type=EventType.TASK_CREATED,
                object_type="Task",
                object_id=str(task.id),
                metadata={
                    "triggered_by_event": event.event_type,
                    "triggered_by_rule": str(rule.id)  # Good practice to track this!
                },
                parent_event=event
            )