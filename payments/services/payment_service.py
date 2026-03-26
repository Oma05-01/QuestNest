# payments/services/payment_service.py
import uuid
from payments.models import Payment
from operations.constants import EventType
from operations.services.event_service import log_event

def pay_rent(*, tenant, tenancy, amount):
    # Added a short UUID to guarantee uniqueness if a payment fails and they retry
    reference = f"RENT-{tenancy.id}-{tenancy.next_payment_date}-{uuid.uuid4().hex[:6]}"

    payment = Payment.objects.create(
        organisation=tenancy.organisation, # Added this since it's on the model
        user=tenant,                       # Fixed: changed 'tenant' to 'user'
        tenancy=tenancy,
        amount=amount,
        reference=reference,
        status=Payment.INITIATED
    )

    log_event(
        organisation=tenancy.organisation,
        actor=tenant,
        event_type=EventType.PAYMENT_INITIATED, # Make sure this is in your constants!
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