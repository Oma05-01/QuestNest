from django.db import transaction
from datetime import timedelta
from django.core.exceptions import ValidationError

from escrow.models import Escrow
from wallet.models import Wallet, WalletTransaction

from operations.services.event_service import log_event
from operations.constants import EventType
from wallet.services.wallet_service import create_wallet_transaction


def create_rent_escrow(*, tenant, tenancy, amount):
    """
    Creates a pending escrow for rent.
    No money moves here.
    """
    # 🟢 CHANGED: Validate against the workspace, not the old organisation model
    if not tenancy.workspace.is_verified:
        raise ValidationError("The workspace managing this tenancy is not verified.")

    # 🟢 CHANGED: Escrow is now linked to workspace and tenancy
    escrow = Escrow.objects.create(
        tenant=tenant,
        workspace=tenancy.workspace,
        tenancy=tenancy,
        amount=amount,
        status=Escrow.PENDING
    )

    log_event(
        workspace=tenancy.workspace,  # 🟢 CHANGED
        actor=tenant,
        event_type=EventType.ESCROW_CREATED,
        object_type="Escrow",
        object_id=str(escrow.id),
        metadata={
            "tenancy_id": str(tenancy.id),
            "amount": str(amount)
        }
    )

    return escrow


@transaction.atomic
def fund_rent_escrow(*, escrow, actor=None):
    """
    Debits tenant wallet and funds escrow.
    """
    if escrow.status != Escrow.PENDING:
        raise ValidationError("Escrow cannot be funded.")

    # 🟢 CHANGED: Safely fetch the Tenant's Personal Wallet
    tenant_wallet = Wallet.objects.filter(user=escrow.tenant, workspace__isnull=True).first()

    if not tenant_wallet or tenant_wallet.balance < escrow.amount:
        raise ValidationError("Insufficient wallet balance.")

    # Debit tenant wallet
    create_wallet_transaction(
        wallet=tenant_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.DEBIT,
        reference=f"Rent escrow #{escrow.id}",
        description=f"Escrow funding for {escrow.tenancy.unit.name}"
    )

    # 🟢 CHANGED: Highly recommend using transition_to so the Rules Engine catches it!
    if hasattr(escrow, 'transition_to'):
        escrow.transition_to(Escrow.FUNDED, actor=actor, event_type=EventType.ESCROW_FUNDED)
    else:
        escrow.status = Escrow.FUNDED
        escrow.save(update_fields=["status"])

    return escrow


@transaction.atomic
def release_rent_escrow(*, escrow, actor=None):
    """
    Releases funds to the Property Manager's Workspace after successful handover.
    """
    if escrow.status != Escrow.FUNDED:
        raise ValidationError("Escrow is not funded.")

    # 🟢 CHANGED: Send money to the Business Workspace Wallet, not the old 'landlord'
    workspace_wallet = Wallet.objects.filter(workspace=escrow.workspace).first()

    if not workspace_wallet:
        raise ValidationError("Workspace wallet not found.")

    # Credit workspace wallet
    create_wallet_transaction(
        wallet=workspace_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.CREDIT,
        reference=f"Rent payout escrow #{escrow.id}",
        description=f"Escrow release for {escrow.tenancy.unit.name}"
    )

    if hasattr(escrow, 'transition_to'):
        escrow.transition_to(Escrow.RELEASED, actor=actor, event_type=EventType.ESCROW_RELEASED)
    else:
        escrow.status = Escrow.RELEASED
        escrow.save(update_fields=["status"])

    return escrow


@transaction.atomic
def refund_rent_escrow(*, escrow, actor=None):
    """
    Refunds tenant if rent fails or dispute is resolved.
    """
    if escrow.status != Escrow.FUNDED:
        raise ValidationError("Escrow cannot be refunded.")

    # 🟢 CHANGED: Explicitly credit the Personal Wallet
    tenant_wallet = Wallet.objects.filter(user=escrow.tenant, workspace__isnull=True).first()

    if not tenant_wallet:
        raise ValidationError("Tenant personal wallet not found.")

    # Credit tenant wallet
    create_wallet_transaction(
        wallet=tenant_wallet,
        amount=escrow.amount,
        transaction_type=WalletTransaction.CREDIT,
        reference=f"Rent refund escrow #{escrow.id}",
        description=f"Escrow refund for {escrow.tenancy.unit.name}"
    )

    if hasattr(escrow, 'transition_to'):
        escrow.transition_to(Escrow.REFUNDED, actor=actor, event_type=EventType.ESCROW_REFUNDED)
    else:
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

    tenancy = current_escrow.tenancy

    # Ensure tenancy is still active
    if tenancy.status != tenancy.ACTIVE:
        raise ValidationError("Tenancy is no longer active for renewal.")

    # Calculate new start and end dates
    new_start_date = current_escrow.end_date + timedelta(days=1)
    new_end_date = new_start_date + timedelta(days=period_days)

    # 🟢 CHANGED: Use tenancy instead of landlord/property
    new_escrow = create_rent_escrow(
        tenant=current_escrow.tenant,
        tenancy=tenancy,
        amount=current_escrow.amount
    )

    # Assign new period
    new_escrow.start_date = new_start_date
    new_escrow.end_date = new_end_date
    new_escrow.save(update_fields=['start_date', 'end_date'])

    return new_escrow