import uuid

from django.db import transaction

from escrow.models import Escrow
from wallet.models import WalletTransaction


def transfer_to_escrow(wallet, amount, escrow, actor=None):
    from operations.services.event_service import log_event
    from operations.constants import EventType

    with transaction.atomic():
        if wallet.balance < amount:
            raise ValueError("Insufficient funds")

        # Debit wallet
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='debit',
            reference=f"ESCROW-FUND-{uuid.uuid4()}",
            description=f"Funding escrow {escrow.id}"
        )

        # Mark escrow funded
        escrow.transition_to(Escrow.FUNDED, actor=actor, event_type=EventType.ESCROW_FUNDED)