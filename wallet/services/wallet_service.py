from django.db import transaction
from wallet.models import WalletTransaction

def create_wallet_transaction(
    *,
    wallet,
    amount,
    transaction_type,
    reference,
    description=""
):
    """
    Safe wallet transaction creator:
    - Prevents duplicates (idempotent)
    - Ensures atomic balance updates
    """

    with transaction.atomic():

        existing = WalletTransaction.objects.filter(reference=reference).first()
        if existing:
            return existing  # Prevent duplicate execution

        # Compute balance safely
        if transaction_type == "debit" and wallet.balance < amount:
            raise ValueError("Insufficient balance.")

        tx = WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=transaction_type,
            reference=reference,
            description=description
        )

        return tx