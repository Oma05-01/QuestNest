from django.db import transaction
from wallet.models import Wallet, WalletTransaction


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
    - Prevents race conditions with database-level row locking 🛡️
    """

    with transaction.atomic():
        # 1. Idempotency: Prevent duplicate execution
        existing = WalletTransaction.objects.filter(reference=reference).first()
        if existing:
            return existing

            # 2. Lock the wallet row strictly for this transaction!
        # If another process tries to touch this wallet, it will wait in line.
        locked_wallet = Wallet.objects.select_for_update().get(id=wallet.id)

        # 3. Compute and apply balance safely using constants
        if transaction_type == WalletTransaction.DEBIT:  # Assuming you have a DEBIT constant
            if locked_wallet.balance < amount:
                raise ValueError("Insufficient balance.")
            locked_wallet.balance -= amount

        elif transaction_type == WalletTransaction.CREDIT:
            locked_wallet.balance += amount

        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        # 4. Save the updated balance to the locked wallet
        locked_wallet.save(update_fields=['balance'])

        # 5. Create the audit ledger record
        tx = WalletTransaction.objects.create(
            wallet=locked_wallet,
            amount=amount,
            transaction_type=transaction_type,
            reference=reference,
            description=description
        )

        return tx