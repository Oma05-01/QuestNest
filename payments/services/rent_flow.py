from django.db import transaction
from datetime import timedelta
from django.core.exceptions import ValidationError

from escrow.models import Escrow
from wallet.models import WalletTransaction

from operations.services.event_service import log_event
from operations.constants import EventType

def create_rent_escrow(*, tenant, landlord, property_obj, amount):
    """
    Creates a pending escrow for rent.
    No money moves here.
    """
    if not property_obj.is_available:
        raise ValidationError("Property is not available for rent.")

    if not property_obj.is_verified:
        raise ValidationError("Property is not verified for rent.")

    if not property_obj.organisation.verified:
        raise ValidationError("Organisation owning this property is not verified.")

    escrow = Escrow.objects.create(
        tenant=tenant,
        landlord=landlord,
        property=property_obj,
        amount=amount,
        status=Escrow.PENDING
    )

    log_event(
        organisation=property_obj.organisation,
        actor=tenant,
        event_type=EventType.ESCROW_CREATED,
        object_type="Escrow",
        object_id=str(escrow.id),
        metadata={
            "property_id": property_obj.id,
            "amount": str(amount)
        }
    )

    return escrow


@transaction.atomic
def fund_rent_escrow(*, escrow):
    """
    Debits tenant wallet and funds escrow.
    """

    if escrow.status != Escrow.PENDING:
        raise ValidationError("Escrow cannot be funded.")

    tenant_wallet = escrow.tenant.wallet

    if tenant_wallet.balance < escrow.amount:
        raise ValidationError("Insufficient wallet balance.")

    # Debit tenant wallet
    WalletTransaction.objects.create(
        wallet=tenant_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.DEBIT,
        reference=f"Rent escrow #{escrow.id}"
    )

    escrow.status = Escrow.FUNDED
    escrow.save(update_fields=["status"])

    return escrow

@transaction.atomic
def release_rent_escrow(*, escrow):
    """
    Releases funds to landlord after successful handover.
    """

    if escrow.status != Escrow.FUNDED:
        raise ValidationError("Escrow is not funded.")

    landlord_wallet = escrow.landlord.wallet

    # Credit landlord wallet
    WalletTransaction.objects.create(
        wallet=landlord_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.CREDIT,
        reference=f"Rent payout escrow #{escrow.id}"
    )

    escrow.status = Escrow.RELEASED
    escrow.save(update_fields=["status"])

    return escrow

@transaction.atomic
def refund_rent_escrow(*, escrow):
    """
    Refunds tenant if rent fails or dispute is resolved.
    """

    if escrow.status != Escrow.FUNDED:
        raise ValidationError("Escrow cannot be refunded.")

    tenant_wallet = escrow.tenant.wallet

    # Credit tenant wallet
    WalletTransaction.objects.create(
        wallet=tenant_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.CREDIT,
        reference=f"Rent refund escrow #{escrow.id}"
    )

    escrow.status = Escrow.REFUNDED
    escrow.save(update_fields=["status"])

    return escrow

def renew_rent_escrow(*, current_escrow, period_days=30):
    """
    Automatically creates a new escrow for the next rent period
    based on the current escrow's end_date.
    """

    if current_escrow.status != Escrow.RELEASED:
        raise ValidationError("Only released escrows can be renewed.")

    property_obj = current_escrow.property

    # Ensure property is available for the next period
    if not property_obj.is_available:
        raise ValidationError("Property is not available for renewal.")

    # Calculate new start and end dates
    new_start_date = current_escrow.end_date + timedelta(days=1)
    new_end_date = new_start_date + timedelta(days=period_days)

    # Create new escrow using existing service
    new_escrow = create_rent_escrow(
        tenant=current_escrow.tenant,
        landlord=current_escrow.landlord,
        property_obj=property_obj,
        amount=current_escrow.amount
    )

    # Assign new period
    new_escrow.start_date = new_start_date
    new_escrow.end_date = new_end_date
    new_escrow.save(update_fields=['start_date', 'end_date'])

    return new_escrow