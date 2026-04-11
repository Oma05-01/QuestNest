from django.db import transaction
from payments.models import Payment
from operations.constants import EventType
from operations.services.event_service import log_event

def pay_rent(*, tenant, tenancy, amount):
    # 1. Deterministic reference for idempotency
    reference = f"PAY-{tenancy.id}-{tenancy.next_payment_date.strftime('%Y%m%d')}"

    # 2. WRAP IN ATOMIC: If rules fail fatally, everything rolls back
    with transaction.atomic():
        payment = Payment.objects.create(
            organisation=tenancy.organisation,
            user=tenant,
            tenancy=tenancy,
            amount=amount,
            reference=reference,
            status=Payment.INITIATED
        )

        log_event(
            organisation=tenancy.organisation,
            actor=tenant,
            event_type=EventType.PAYMENT_INITIATED,
            object_type="Payment",
            object_id=str(payment.id),
            metadata={
                "payment_id": str(payment.id),
                "tenancy_id": str(tenancy.id),
                "amount": str(amount),
                "reference": reference
            }
        )

    return payment