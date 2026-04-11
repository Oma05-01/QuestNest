import pytest
from decimal import Decimal
from payments.models import Payment
from operations.models import Event
from operations.services.event_service import log_event
from operations.constants import EventType

@pytest.mark.django_db
class TestRuleEngineLogic:

    def test_rule_aborts_if_wrong_condition(self, active_tenancy, funded_tenant):
        """
        Tests the `activate_tenancy_after_payment` rule.
        It should abort and do nothing if the Payment status is NOT 'success'.
        """
        # 1. SETUP: Tenancy starts as 'pending'
        active_tenancy.status = "pending"
        active_tenancy.save()

        # Create a payment that FAILED
        payment = Payment.objects.create(
            organisation=active_tenancy.organisation,
            user=funded_tenant,
            tenancy=active_tenancy,
            amount=Decimal("1000.00"),
            reference="TEST-REF-FAIL",
            status=Payment.FAILED  # 🔴 This is the wrong condition!
        )

        # 2. TRIGGER: Fake the ESCROW_FUNDED event
        # We simulate the Escrow being funded anyway to see if the rule catches the failed payment
        log_event(
            organisation=active_tenancy.organisation,
            actor=funded_tenant,
            event_type="ESCROW_FUNDED",
            object_type="Tenancy",  # We map it to tenancy for the test
            object_id=str(active_tenancy.id),
            metadata={"payment_id": str(payment.id)}
        )

        # 3. ASSERT: The tenancy should STILL be pending because the rule aborted
        active_tenancy.refresh_from_db()
        assert active_tenancy.status == "pending"

    def test_late_fee_chain_reaction(self, active_tenancy):
        # 1. Setup
        active_tenancy.late_fee_amount = Decimal("500.00")
        active_tenancy.late_fee_applied = False
        active_tenancy.save()

        # 2. Trigger
        event = log_event(
            organisation=active_tenancy.organisation,
            event_type=EventType.RENT_OVERDUE,
            object_type="Tenancy",
            object_id=str(active_tenancy.id)
        )

        # 🟢 REFRESH THE EVENT!
        # Without this, event.metadata will always be {} in the test.
        event.refresh_from_db()

        # 3. Assertions
        if active_tenancy.late_fee_applied is False:
            print(f"DEBUG: Event Status: {event.status}")
            print(f"DEBUG: Event Metadata: {event.metadata}")
            # Refresh tenancy to see if the rule changed it in the DB
            active_tenancy.refresh_from_db()

        assert active_tenancy.late_fee_applied is True