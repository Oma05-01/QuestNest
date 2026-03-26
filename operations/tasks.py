from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from operations.models import Event, EventRule
from operations.services.reconciliation_service import reconcile_payment_event
from operations.services.task_service import create_task
from operations.utils import get_object_from_event, format_dynamic_text
from django.utils import timezone
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

    try:
        # Fetch active rules (global + org-specific)
        rules = EventRule.objects.filter(
            event_type=event.event_type,
            is_active=True
        ).filter(
            Q(organisation=event.organisation) | Q(organisation__isnull=True)
        ).order_by("execution_order")

        for rule in rules:
            if rule.action_type == "CREATE_TASK":
                raw_title = rule.action_payload.get("title", "System Task")
                raw_description = rule.action_payload.get("description", "")

                related_object = get_object_from_event(event)

                parsed_title = format_dynamic_text(raw_title, related_object)
                parsed_description = format_dynamic_text(raw_description, related_object)

                create_task(
                    organisation=event.organisation,
                    title=parsed_title,
                    description=parsed_description,
                    related_object_type=event.object_type,
                    related_object_id=event.object_id,
                    parent_event=event
                )

        # ✅ mark success
        if hasattr(event, "status"):
            event.status = "processed"
            event.save(update_fields=["status"])

    except Exception as e:
        # ❌ mark failure
        if hasattr(event, "status"):
            event.status = "failed"
            event.save(update_fields=["status"])

        raise  # let Celery handle retry if configured

@shared_task
def reconcile_failed_events():
    from operations.models import Event

    failed_events = Event.objects.filter(status="failed")

    for event in failed_events:
        try:
            reconcile_payment_event(event)
        except Exception:
            continue

@shared_task
def trigger_due_rent_payments():
    from rentals.models import Tenancy
    from operations.services.event_service import log_event

    today = timezone.now().date()

    tenancies = Tenancy.objects.filter(
        status=Tenancy.ACTIVE,
        next_payment_date__isnull=False
    )

    for tenancy in tenancies:
        due_date = tenancy.next_payment_date
        grace_limit = due_date + timedelta(days=tenancy.grace_period_days)

        if today == due_date:
            log_event(
                organisation=tenancy.organisation,
                actor=tenancy.tenant,
                event_type=EventType.RENT_PAYMENT_DUE,
                object_type="Tenancy",
                object_id=str(tenancy.id),
                metadata={
                    "tenancy_id": str(tenancy.id),
                    "amount": str(tenancy.rent_amount)
                }
            )

        elif today > grace_limit and not tenancy.late_fee_applied:
            log_event(
                organisation=tenancy.organisation,
                actor=tenancy.tenant,
                event_type=EventType.RENT_OVERDUE,
                object_type="Tenancy",
                object_id=str(tenancy.id),
                metadata={
                    "tenancy_id": str(tenancy.id),
                    "amount": str(tenancy.rent_amount)
                }
            )

@shared_task
def retry_payment_task(payment_id):
    from payments.models import Payment
    from operations.services.event_service import log_event
    from operations.constants import EventType

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return

    if payment.status != Payment.FAILED:
        return

    log_event(
        organisation=payment.organisation,
        actor=payment.user,
        event_type=EventType.PAYMENT_INITIATED,
        object_type="Payment",
        object_id=str(payment.id),
        metadata={
            "payment_id": str(payment.id),
            "tenancy_id": str(payment.tenancy.id),
            "amount": str(payment.amount),
            "reference": payment.reference
        }
    )