from datetime import timedelta
from celery import shared_task
from django.db.models import Q
from django.utils import timezone
import logging

from operations.models import Event, EventRule
from operations.services.reconciliation_service import reconcile_payment_event
from operations.constants import EventType

logger = logging.getLogger(__name__)

@shared_task
def process_event_rules_task(event_id):
    """
    Processes rules for a specific event.
    Synchronizes hardcoded business logic with dynamic DB rules.
    """
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    try:
        # 1. Execute Hardcoded Logic (The 'Gears')
        from operations.rules import execute_rules
        execute_rules(event)

        event.refresh_from_db()
        if event.status == "failed":
            return

        # 2. Execute Dynamic DB Rules (The 'Customizations')
        rules = EventRule.objects.filter(
            event_type=event.event_type,
            is_active=True
        ).filter(
            Q(organisation=event.organisation) | Q(organisation__isnull=True)
        ).order_by("execution_order")

        for rule in rules:
            # (Your task creation logic goes here)
            pass

        event.status = "processed"
        event.save(update_fields=["status"])

    except Exception as e:
        logger.error(f"Error processing event {event_id}: {e}")
        event.status = "failed"
        event.save(update_fields=["status"])
        raise

@shared_task
def trigger_due_rent_payments():
    from rentals.models import Tenancy
    """
    The Midnight Scan: Proactively identifies due and overdue rent.
    Only processes for VERIFIED organisations.
    """
    from operations.services.event_service import log_event

    today = timezone.now().date()

    # 🟢 Optimization: Filter by ACTIVE tenancies in VERIFIED orgs
    tenancies = Tenancy.objects.filter(
        status=Tenancy.ACTIVE,
        next_payment_date__isnull=False,
        organisation__is_verified=True # 🛡️ The Security Gate
    ).select_related('organisation', 'tenant')

    for tenancy in tenancies:
        due_date = tenancy.next_payment_date
        # Grace period logic: e.g., Due on 1st + 5 days grace = Overdue on 6th
        grace_limit = due_date + timedelta(days=tenancy.grace_period_days)

        # SCENARIO A: It's Due Day
        if today == due_date:
            log_event(
                organisation=tenancy.organisation,
                actor=tenancy.tenant,
                event_type=EventType.RENT_PAYMENT_DUE,
                object_type="Tenancy",
                object_id=str(tenancy.id),
                metadata={
                    "tenancy_id": str(tenancy.id),
                    "amount": str(tenancy.rent_amount),
                    "due_date": str(due_date)
                }
            )

        # SCENARIO B: It's Overdue (Past Grace Period)
        elif today > grace_limit and not tenancy.late_fee_applied:
            log_event(
                organisation=tenancy.organisation,
                actor=tenancy.tenant,
                event_type=EventType.RENT_OVERDUE,
                object_type="Tenancy",
                object_id=str(tenancy.id),
                metadata={
                    "tenancy_id": str(tenancy.id),
                    "amount": str(tenancy.rent_amount),
                    "days_late": (today - due_date).days
                }
            )

@shared_task
def reconcile_failed_events():
    """Cleanup task for events that stalled or crashed."""
    failed_events = Event.objects.filter(status="failed")
    for event in failed_events:
        try:
            reconcile_payment_event(event)
        except Exception as e:
            logger.warning(f"Reconciliation failed for event {event.id}: {e}")
            continue


@shared_task
def retry_payment_task(payment_id):
    """Retries a failed payment by logging a new initiation event."""
    from payments.models import Payment
    from operations.services.event_service import log_event
    try:
        payment = Payment.objects.get(id=payment_id)
        if payment.status == Payment.FAILED:
            log_event(
                organisation=payment.organisation,
                actor=payment.user,
                event_type=EventType.PAYMENT_INITIATED,
                object_type="Payment",
                object_id=str(payment.id),
                metadata={"payment_id": str(payment.id), "amount": str(payment.amount)}
            )
    except Payment.DoesNotExist:
        pass