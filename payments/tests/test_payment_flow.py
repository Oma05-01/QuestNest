import pytest
from decimal import Decimal
from unittest.mock import patch
from django.db import InternalError

from operations.models import Event
from payments.models import Payment
from escrow.models import Escrow
from wallet.models import WalletTransaction
from payments.services.payment_service import pay_rent


# @pytest.mark.django_db tells pytest this test needs database access
@pytest.mark.django_db
def test_successful_rent_payment_integration(funded_tenant, active_tenancy):
    """
    INTEGRATION TEST:
    Verifies that pay_rent() synchronizes Wallet, Escrow, Payment, and Events.
    """
    initial_balance = funded_tenant.wallet.balance  # 5000.00
    rent_amount = Decimal("1000.00")

    # 1. THE ACTION
    # This triggers: Payment Created -> Event Logged -> Rules Fired -> Wallet Debited -> Escrow Funded
    payment = pay_rent(tenant=funded_tenant, tenancy=active_tenancy, amount=rent_amount)

    # 2. REFRESH DATA (The "Magic" Line)
    # We MUST tell these objects to look at the database again to see what the rules did.
    payment.refresh_from_db()
    funded_tenant.wallet.refresh_from_db()
    active_tenancy.refresh_from_db()

    # 3. THE CHAIN REACTION ASSERTIONS

    # A. Wallet Integrity: 5000 - 1000 = 4000
    assert funded_tenant.wallet.balance == Decimal("4000.00")
    assert WalletTransaction.objects.filter(
        wallet=funded_tenant.wallet,
        transaction_type=WalletTransaction.DEBIT,
        amount=rent_amount
    ).exists()

    # B. Payment Status: Verified that rules successfully transitioned the status
    assert payment.status == Payment.SUCCESS
    assert payment.amount == rent_amount

    # C. Escrow Funding: Verified that the 'fund_escrow_on_payment' rule worked
    escrow = Escrow.objects.filter(metadata__payment_id=str(payment.id)).first()
    assert escrow is not None
    assert escrow.status == Escrow.FUNDED
    assert escrow.amount == rent_amount

    # D. Event Ledger: Verified that 'mark_payment_success' rule logged the final event
    assert Event.objects.filter(
        object_id=str(payment.id),
        event_type="PAYMENT_SUCCESS"
    ).exists()


@pytest.mark.django_db
def test_insufficient_funds_payment_flow(funded_tenant, active_tenancy):
    """
    Tests the failure path: Tenant tries to pay MORE than they have.
    """
    # Tenant only has 5000 from our fixture
    rent_amount = Decimal("6000.00")

    # Action
    payment = pay_rent(
        tenant=funded_tenant,
        tenancy=active_tenancy,
        amount=rent_amount
    )

    payment.refresh_from_db()
    funded_tenant.wallet.refresh_from_db()

    # Assertions
    # Payment should have been failed by `validate_payment_balance` rule
    assert payment.status == Payment.FAILED

    # Wallet should NOT be debited
    assert funded_tenant.wallet.balance == Decimal("5000.00")

    # Escrow should NOT exist for this payment
    assert not Escrow.objects.filter(metadata__payment_id=str(payment.id)).exists()


@pytest.mark.django_db
def test_pay_rent_creates_correct_event(funded_tenant, active_tenancy):
    # 1. Action
    payment = pay_rent(
        tenant=funded_tenant,
        tenancy=active_tenancy,
        amount=Decimal("1000.00")
    )

    # 2. Assertions
    # 🟢 FIX: Specify the event_type so we don't accidentally grab the 'Success' event
    event = Event.objects.get(
        object_id=str(payment.id),
        event_type="PAYMENT_INITIATED"
    )

    assert event is not None
    assert event.actor == funded_tenant
    assert event.metadata["amount"] == "1000.00"
    # Depending on your engine, the initiation event might be marked 'processed'
    # as soon as the rules finish running.
    assert event.status in ["pending", "processed"]


@pytest.mark.django_db
def test_payment_rollback_on_escrow_failure(funded_tenant, active_tenancy):
    initial_balance = funded_tenant.wallet.balance

    # 🟢 FIX: Point directly to escrow.models, NOT operations.rules
    with patch('escrow.models.Escrow.objects.create') as mocked_create:
        mocked_create.side_effect = Exception("Database Crash!")

        # We don't use 'pytest.raises' because execute_rules catches the error
        payment = pay_rent(
            tenant=funded_tenant,
            tenancy=active_tenancy,
            amount=Decimal("1000.00")
        )

    # 3. VERIFY: The engine should have caught the mock error
    from operations.models import Event
    event = Event.objects.get(
        object_id=str(payment.id),
        event_type="PAYMENT_INITIATED"
    )

    # Refresh the wallet to ensure no money left the building
    funded_tenant.wallet.refresh_from_db()

    assert event.status == "failed"
    assert "error_create_escrow_on_payment" in event.metadata
    assert funded_tenant.wallet.balance == initial_balance