from datetime import timedelta

from operations.models import Task, RuleExecution
from operations.constants import EventType
from operations.services.event_service import log_event
from collections import defaultdict

def task_exists(organisation, title, related_object_type, related_object_id):
    return Task.objects.filter(
        organisation=organisation,
        title=title,
        related_object_type=related_object_type,
        related_object_id=str(related_object_id)
    ).exists()


def rule_already_executed(event, rule_name):
    return RuleExecution.objects.filter(
        event=event,
        rule_name=rule_name
    ).exists()


def mark_rule_executed(event, rule_name):
    RuleExecution.objects.create(
        event=event,
        rule_name=rule_name
    )

# ------------------------
# Rule Registry
# ------------------------
_RULES_REGISTRY = defaultdict(list)

def register_rule(trigger_event, priority=100):
    """
    Decorator to register a function as a rule for a specific event type.
    """
    def decorator(func):
        _RULES_REGISTRY[trigger_event].append((priority, func))
        return func
    return decorator

def execute_rules(event, visited=None):
    """
    Execute all rules registered for this event type.
    """
    # Simply trigger registered rules. No hard-coded logic here!
    if visited is None:
        visited = set()

        # Prevent circular execution
    if event.id in visited:
        return

    visited.add(event.id)

    rules = _RULES_REGISTRY.get(event.event_type, [])

    # Sort by priority (lower number runs first)
    sorted_rules = sorted(rules, key=lambda x: x[0])

    for _, rule in sorted_rules:

        rule_name = rule.__name__

        if rule_already_executed(event, rule_name):
            continue

        rule(event, visited=visited)

        mark_rule_executed(event, rule_name)

# ------------------------
# Registered Rules
# ------------------------
@register_rule(EventType.PAYMENT_INITIATED, priority=5)
def validate_payment_balance(event, visited=None):
    from payments.models import Payment

    metadata = event.metadata or {}
    payment_id = metadata.get("payment_id")

    if not payment_id:
        return

    payment = Payment.objects.get(id=payment_id)

    # Already failed or processed → do nothing (idempotent)
    if payment.status != Payment.INITIATED:
        return

    tenant_wallet = payment.user.wallet

    if tenant_wallet.balance < payment.amount:
        payment.transition_to(
            Payment.FAILED,
            actor=event.actor,
            event_type=EventType.PAYMENT_FAILED,
            metadata={
                "reason": "insufficient_balance"
            }
        )

@register_rule(EventType.PAYMENT_INITIATED, priority=10)
def create_escrow_on_payment(event, visited=None):
    from escrow.models import Escrow
    from rentals.models import Tenancy

    metadata = event.metadata or {}

    tenancy_id = metadata.get("tenancy_id")
    amount = metadata.get("amount")
    payment_id = metadata.get("payment_id")
    reference = metadata.get("reference")

    if not tenancy_id or not amount or not payment_id:
        return

    tenancy = Tenancy.objects.get(id=tenancy_id)

    # ✅ Strong idempotency: tie escrow to payment_id
    existing = Escrow.objects.filter(
        tenancy=tenancy,
        metadata__payment_id=payment_id
    ).first()

    if existing:
        return existing

    escrow = Escrow.objects.create(
        tenant=tenancy.tenant,
        landlord=tenancy.unit.asset.owner,
        tenancy=tenancy,
        amount=amount,
        status=Escrow.PENDING,
        organisation=tenancy.organisation,
        metadata={
            "payment_id": payment_id,
            "reference": reference
        }
    )

    return escrow

@register_rule(EventType.LEASE_SIGNED, priority=10)
def create_tenancy_from_lease(event, visited=None):
    from leases.models import LeaseAgreement
    from rentals.models import Tenancy

    lease = event.object

    # ✅ idempotency: prevent duplicate tenancy
    existing = Tenancy.objects.filter(
        unit=lease.unit,
        tenant=lease.tenant,
        start_date=lease.start_date
    ).first()

    if existing:
        return existing

    tenancy = Tenancy.objects.create(
        organisation=lease.organisation,
        unit=lease.unit,
        tenant=lease.tenant,
        start_date=lease.start_date,
        end_date=lease.end_date,
        status=Tenancy.PENDING
    )

    return tenancy

@register_rule(EventType.LEASE_SIGNED, priority=20)
def trigger_payment_for_lease(event, visited=None):
    from leases.models import LeaseAgreement
    from rentals.models import Tenancy
    from payments.services.payment_service import pay_rent

    lease = event.object

    tenancy = Tenancy.objects.filter(
        unit=lease.unit,
        tenant=lease.tenant,
        start_date=lease.start_date
    ).first()

    if not tenancy:
        return

    # Optional: prevent duplicate payment
    if tenancy.payments.filter(status="initiated").exists():
        return

    pay_rent(
        tenant=lease.tenant,
        tenancy=tenancy,
        amount=lease.amount  # or lease.rent_amount
    )

@register_rule(EventType.PAYMENT_INITIATED, priority=20)
def fund_escrow_on_payment(event, visited=None):
    from escrow.models import Escrow
    from payments.models import Payment
    from wallet.models import WalletTransaction
    from wallet.services.wallet_service import create_wallet_transaction

    metadata = event.metadata or {}

    tenancy_id = metadata.get("tenancy_id")
    amount = metadata.get("amount")
    payment_id = metadata.get("payment_id")
    reference = metadata.get("reference")

    if not tenancy_id or not amount or not payment_id:
        return

    payment = Payment.objects.get(id=payment_id)

    # 🚨 CRITICAL GUARD
    if payment.status == Payment.FAILED:
        return

    escrow = Escrow.objects.filter(
        tenancy_id=tenancy_id,
        metadata__payment_id=payment_id,
        status=Escrow.PENDING
    ).first()

    if not escrow:
        return

    tenant_wallet = escrow.tenant.wallet

    try:
        # ✅ Idempotent debit (reference MUST be unique)
        create_wallet_transaction(
            wallet=tenant_wallet,
            amount=amount,
            transaction_type=WalletTransaction.DEBIT,
            reference=reference,
            description=f"Rent payment for {escrow.tenancy.unit.name}"
        )

        # ✅ Transition escrow → FUNDED
        if escrow.status != Escrow.FUNDED:
            escrow.transition_to(
                Escrow.FUNDED,
                actor=event.actor,
                event_type=EventType.ESCROW_FUNDED,
                metadata={
                    "payment_id": payment_id,
                    "reference": reference
                }
            )
    except Exception:
        payment.transition_to(
            Payment.FAILED,
            actor=event.actor,
            event_type=EventType.PAYMENT_FAILED,
            metadata={
                "reason": "wallet_error"
            }
        )
        return

@register_rule(EventType.ESCROW_FUNDED, priority=40)
def mark_payment_success(event, visited=None):
    from payments.models import Payment

    payment_id = event.metadata.get("payment_id")
    if not payment_id:
        return

    payment = Payment.objects.get(id=payment_id)

    if payment.status == Payment.SUCCESS:
        return

    payment.transition_to(
        Payment.SUCCESS,
        actor=event.actor,
        event_type=EventType.PAYMENT_SUCCESS,
        metadata={
            "payment_id": payment_id
        }
    )

@register_rule(EventType.ESCROW_FUNDED, priority=50)
def activate_tenancy_after_payment(event, visited=None):
    from payments.models import Payment

    escrow = event.object
    tenancy = escrow.tenancy

    payment_id = event.metadata.get("payment_id")
    if not payment_id:
        return

    payment = Payment.objects.get(id=payment_id)

    # 🔥 HARD ENFORCEMENT
    if payment.status != Payment.SUCCESS:
        return

    if tenancy.status != tenancy.ACTIVE:
        tenancy.transition_to(
            tenancy.ACTIVE,
            actor=event.actor,
            event_type=EventType.TENANCY_ACTIVATED
        )

@register_rule(EventType.PAYMENT_FAILED)
def mark_payment_failed(event):
    from payments.models import Payment

    payment_id = event.metadata.get("payment_id")

    payment = Payment.objects.get(id=payment_id)

    payment.status = Payment.status.FAILED
    payment.save(update_fields=["status"])

@register_rule(EventType.ASSET_STATUS_CHANGED)
def create_tenancy_agreement_task(event, visited=None):
    """Extracted from the hard-coded block"""
    if event.metadata.get("to") == "reserved":
        task = Task.objects.create(
            organisation=event.organisation,
            title="Prepare tenancy agreement",
            related_object_type=event.object_type, # Or Property, depending on your rename
            related_object_id=event.object_id,
            created_by=None
        )

        log_event(
            organisation=event.organisation,
            actor=None,
            event_type=EventType.TASK_CREATED,
            object_type="Task",
            object_id=str(task.id),
            metadata={"triggered_by_event": event.event_type},
            parent_event=event
        )

@register_rule(EventType.ESCROW_FUNDED)
def escrow_funded_reserve_unit(event, visited=None):
    # Fetch the actual object using the ID
    escrow = event.object
    unit = escrow.tenancy.unit

    if unit.status != unit.RESERVED:
        unit.transition_to(
            unit.RESERVED,
            actor=event.actor,
            event_type=EventType.UNIT_RESERVED,
        )

@register_rule(EventType.ESCROW_RELEASED)
def escrow_released_occupy_unit(event, visited=None):
    # Fetch the actual object using the ID
    escrow = event.object
    unit = escrow.tenancy.unit

    if unit.status != unit.OCCUPIED:
        unit.transition_to(
            unit.OCCUPIED,
            actor=event.actor,
            event_type=EventType.UNIT_OCCUPIED,
        )

@register_rule(EventType.ESCROW_FUNDED)
def activate_tenancy_on_payment(event, visited=None):
    from payments.models import Payment

    escrow = event.object
    tenancy = escrow.tenancy

    payment_id = event.metadata.get("payment_id")

    if not payment_id:
        return  # safety guard

    payment = Payment.objects.get(id=payment_id)

    # 🔥 enforce payment success
    if payment.status != Payment.SUCCESS:
        return

    if tenancy.status != tenancy.ACTIVE:
        tenancy.transition_to(
            tenancy.ACTIVE,
            actor=event.actor,
            event_type=EventType.TENANCY_ACTIVATED
        )

@register_rule(EventType.TENANCY_ACTIVATED, priority=10)
def mark_unit_occupied(event, visited=None):
    tenancy = event.object
    unit = tenancy.unit

    if unit.status != unit.OCCUPIED:
        unit.transition_to(
            unit.OCCUPIED,
            actor=event.actor,
            event_type=EventType.UNIT_OCCUPIED
        )

@register_rule(EventType.ESCROW_FUNDED)
def create_verification_task(event, visited=None):
    escrow = event.object

    task = Task.objects.create(
        organisation=escrow.organisation,
        title=f"Verify unit {escrow.unit.name} for move-in",
        related_object_type="Escrow",
        related_object_id=str(escrow.id),
        created_by=None
    )

    log_event(
        organisation=escrow.organisation,
        actor=None,
        event_type=EventType.TASK_CREATED,
        object_type="Task",
        object_id=str(task.id),
        metadata={"triggered_by_event": event.event_type},
        parent_event=event
    )

@register_rule(EventType.TENANCY_ACTIVATED, priority=20)
def set_initial_payment_date(event, visited=None):
    tenancy = event.object

    if tenancy.next_payment_date:
        return  # idempotent

    tenancy.next_payment_date = tenancy.start_date
    tenancy.save(update_fields=["next_payment_date"])

@register_rule(EventType.LEASE_SIGNED, priority=50)
def create_lease_move_in_preparation_task(event, visited=None):

    Task.objects.create(
        organisation=event.organisation,
        title="Prepare property for tenant move-in",
        related_object_type="Lease",
        related_object_id=str(event.object_id)
    )

@register_rule(EventType.LEASE_CREATED)
def auto_generate_lease_pdf(event, visited=None):

    from leases.models import LeaseAgreement
    from leases.services.lease_pdf_service import generate_lease_pdf

    lease = LeaseAgreement.objects.get(id=event.object_id)

    generate_lease_pdf(lease)

@register_rule(EventType.ESCROW_RELEASE_REQUESTED, priority=10)
def release_escrow_on_request(event, visited=None):
    from escrow.models import Escrow
    from wallet.services.wallet_service import create_wallet_transaction
    from wallet.models import WalletTransaction

    escrow = Escrow.objects.get(id=event.object_id)

    if escrow.status != Escrow.FUNDED:
        return

    landlord_wallet = escrow.landlord.wallet

    create_wallet_transaction(
        wallet=landlord_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.CREDIT,
        reference=f"ESCROW-RELEASE-{escrow.id}",
        description=f"Escrow release for {escrow.unit.name}"
    )

    escrow.release(actor=event.actor)

@register_rule(EventType.ESCROW_REFUND_REQUESTED, priority=10)
def refund_escrow_on_request(event, visited=None):
    from escrow.models import Escrow
    from wallet.services.wallet_service import create_wallet_transaction
    from wallet.models import WalletTransaction

    escrow = Escrow.objects.get(id=event.object_id)

    if escrow.status != Escrow.FUNDED:
        return

    tenant_wallet = escrow.tenant.wallet

    create_wallet_transaction(
        wallet=tenant_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.CREDIT,
        reference=f"ESCROW-REFUND-{escrow.id}",
        description=f"Escrow refund for {escrow.unit.name}"
    )

    escrow.refund(actor=event.actor)

@register_rule(EventType.RENT_PAYMENT_DUE, priority=10)
def initiate_rent_payment(event, visited=None):
    from payments.services.payment_service import pay_rent
    from rentals.models import Tenancy

    tenancy_id = event.metadata.get("tenancy_id")
    if not tenancy_id:
        return

    tenancy = Tenancy.objects.get(id=tenancy_id)

    # Prevent duplicate payments for same cycle
    existing = tenancy.payments.filter(
        reference__contains=str(tenancy.next_payment_date)
    ).exists()

    if existing:
        return

    pay_rent(
        tenant=tenancy.tenant,
        tenancy=tenancy,
        amount=getattr(tenancy, "rent_amount", 0)
    )

@register_rule(EventType.PAYMENT_SUCCESS, priority=60)
def update_next_payment_date(event, visited=None):
    from payments.models import Payment
    from datetime import timedelta

    payment = event.object
    tenancy = payment.tenancy

    if not tenancy:
        return

    tenancy.next_payment_date = (
        tenancy.next_payment_date + timedelta(days=tenancy.rent_cycle_days)
    )

    tenancy.save(update_fields=["next_payment_date"])

@register_rule(EventType.PAYMENT_FAILED, priority=10)
def schedule_payment_retry(event, visited=None):
    from payments.models import Payment
    from django.utils import timezone
    from datetime import timedelta

    payment = event.object

    # Limit retries
    if payment.retry_count >= 3:
        return

    payment.retry_count += 1
    payment.last_retry_at = timezone.now()
    payment.save(update_fields=["retry_count", "last_retry_at"])

    # Schedule retry event (via Celery delay)
    from operations.tasks import retry_payment_task

    retry_payment_task.apply_async(
        args=[payment.id],
        countdown=60 * 60 * 6  # retry in 6 hours
    )

@register_rule(EventType.RENT_PAYMENT_DUE, priority=5)
def check_grace_period(event, visited=None):
    from django.utils import timezone
    from rentals.models import Tenancy

    tenancy = event.object
    today = timezone.now().date()

    due_date = tenancy.next_payment_date
    grace_limit = due_date + timedelta(days=tenancy.grace_period_days)

    if today <= grace_limit:
        return  # still in grace → allow retry flow

@register_rule(EventType.RENT_OVERDUE, priority=10)
def apply_late_fee(event, visited=None):
    from rentals.models import Tenancy

    tenancy = event.object

    # ✅ idempotency
    if tenancy.late_fee_applied:
        return

    if tenancy.late_fee_amount <= 0:
        return

    tenancy.late_fee_applied = True
    tenancy.save(update_fields=["late_fee_applied"])

    from operations.services.event_service import log_event
    from operations.constants import EventType

    log_event(
        organisation=tenancy.organisation,
        actor=tenancy.tenant,
        event_type=EventType.LATE_FEE_APPLIED,
        object_type="Tenancy",
        object_id=str(tenancy.id),
        metadata={
            "tenancy_id": str(tenancy.id),
            "late_fee": str(tenancy.late_fee_amount)
        }
    )

@register_rule(EventType.LATE_FEE_APPLIED, priority=20)
def create_late_fee_payment(event, visited=None):
    from payments.services.payment_service import pay_rent
    from rentals.models import Tenancy

    tenancy = event.object

    pay_rent(
        tenant=tenancy.tenant,
        tenancy=tenancy,
        amount=tenancy.late_fee_amount
    )

@register_rule(EventType.PAYMENT_SUCCESS, priority=70)
def clear_late_fee_flag(event, visited=None):
    payment = event.object
    tenancy = payment.tenancy

    if not tenancy:
        return

    if tenancy.late_fee_applied:
        tenancy.late_fee_applied = False
        tenancy.save(update_fields=["late_fee_applied"])

@register_rule(EventType.PAYMENT_INITIATED, priority=100)
def notify_payment_initiated(event, visited=None):
    from notifications.services.notification_service import create_notification
    from payments.models import Payment

    payment = event.object

    create_notification(
        user=payment.user,
        organisation=payment.organisation,
        title="Payment Started",
        message=f"Your rent payment of {payment.amount} has been initiated.",
        notification_type="info",
        metadata={"payment_id": payment.id}
    )

@register_rule(EventType.PAYMENT_FAILED, priority=100)
def notify_payment_failed(event, visited=None):
    from notifications.services.notification_service import create_notification

    payment = event.object

    create_notification(
        user=payment.user,
        organisation=payment.organisation,
        title="Payment Failed",
        message="Your payment failed. We will retry automatically.",
        notification_type="error",
        metadata={"payment_id": payment.id}
    )

@register_rule(EventType.PAYMENT_SUCCESS, priority=100)
def notify_payment_success(event, visited=None):
    from notifications.services.notification_service import create_notification

    payment = event.object

    create_notification(
        user=payment.user,
        organisation=payment.organisation,
        title="Payment Successful",
        message=f"Your payment of {payment.amount} was successful.",
        notification_type="success",
        metadata={"payment_id": payment.id}
    )

@register_rule(EventType.RENT_PAYMENT_DUE, priority=90)
def notify_rent_due(event, visited=None):
    from notifications.services.notification_service import create_notification

    tenancy = event.object

    create_notification(
        user=tenancy.tenant,
        organisation=tenancy.organisation,
        title="Rent Due",
        message=f"Your rent of {tenancy.rent_amount} is due today.",
        notification_type="warning",
        metadata={"tenancy_id": tenancy.id}
    )

@register_rule(EventType.LATE_FEE_APPLIED, priority=100)
def notify_late_fee(event, visited=None):
    from notifications.services.notification_service import create_notification

    tenancy = event.object

    create_notification(
        user=tenancy.tenant,
        organisation=tenancy.organisation,
        title="Late Fee Applied",
        message=f"A late fee of {tenancy.late_fee_amount} has been applied.",
        notification_type="error",
        metadata={"tenancy_id": tenancy.id}
    )