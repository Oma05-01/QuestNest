import pytest
from decimal import Decimal
from payments.models import Payment
from operations.models import Event, RuleExecution
from operations.services.event_service import log_event
from operations.rules import execute_rules


@pytest.mark.django_db
def test_rule_cannot_execute_twice_for_same_event(funded_tenant, active_tenancy):
    """
    Ensures that if the engine is triggered multiple times for one event,
    the wallet is only debited once.
    """
    initial_balance = funded_tenant.wallet.balance  # 5000.00
    rent_amount = Decimal("1000.00")

    # 1. Create a REAL payment record so the rules can find it
    payment = Payment.objects.create(
        organisation=active_tenancy.organisation,
        user=funded_tenant,
        tenancy=active_tenancy,
        amount=rent_amount,
        reference="UNIQUE-REF-123",
        status=Payment.INITIATED
    )

    # 2. Log the event manually (This will trigger the rules ONCE via Celery Eager)
    event = log_event(
        organisation=active_tenancy.organisation,
        actor=funded_tenant,
        event_type="PAYMENT_INITIATED",
        object_type="Payment",
        object_id=str(payment.id),
        metadata={
            "payment_id": str(payment.id),
            "amount": str(rent_amount),
            "reference": payment.reference,
            "tenancy_id": str(active_tenancy.id)
        }
    )

    # 3. Simulate the engine running AGAIN for the same event (The "Double Trigger")
    execute_rules(event)

    # 4. ASSERTIONS
    funded_tenant.wallet.refresh_from_db()

    # It should only have been debited ONCE (5000 - 1000 = 4000)
    # If idempotency failed, it would be 3000.00
    assert funded_tenant.wallet.balance == Decimal("4000.00")

    # Verify that the RuleExecution table blocked the second attempt
    # (1 record per rule, per event)
    debit_executions = RuleExecution.objects.filter(
        event=event,
        rule_name="fund_escrow_on_payment"
    ).count()
    assert debit_executions == 1