from celery import shared_task
from django.db.models import Q
from operations.models import Event, EventRule
from operations.services.task_service import create_task
from operations.utils import get_object_from_event, format_dynamic_text

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
            # 1. Get the raw text from the JSON payload (or default to empty string)
            raw_title = rule.action_payload.get("title", "System Task")
            raw_description = rule.action_payload.get("description", "")

            # 2. Fetch the actual object (e.g., the Escrow instance)
            related_object = get_object_from_event(event)

            # 3. Parse the strings
            parsed_title = format_dynamic_text(raw_title, related_object)
            parsed_description = format_dynamic_text(raw_description, related_object)

            # 4. Create the task
            create_task(
                organisation=event.organisation,
                title=parsed_title,
                description=parsed_description,
                related_object_type=event.object_type,
                related_object_id=event.object_id,
                parent_event=event
            )
