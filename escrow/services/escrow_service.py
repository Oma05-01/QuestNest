from django.db import transaction
from django.core.exceptions import ValidationError
from wallet.models import Wallet, WalletTransaction
from escrow.models import Escrow

class EscrowService:
    @staticmethod
    def fund_escrow_from_wallet(escrow_id, actor):
        """
        Moves money from a Tenant's Wallet into an Escrow record.
        """
        with transaction.atomic():
            # 1. Fetch the escrow and lock the row for update to prevent race conditions
            escrow = Escrow.objects.select_for_update().get(id=escrow_id)

            if escrow.status != Escrow.PENDING:
                raise ValidationError("This escrow has already been funded or processed.")

            # 2. Get the Tenant's wallet
            tenant_wallet = Wallet.objects.select_for_update().get(user=escrow.tenant)

            # 3. Check if they have enough money
            if tenant_wallet.balance < escrow.amount:
                raise ValidationError(
                    f"Insufficient funds. Required: ₦{escrow.amount}, "
                    f"Available: ₦{tenant_wallet.balance}"
                )

            # 4. Create the Debit Transaction
            WalletTransaction.objects.create(
                wallet=tenant_wallet,
                amount=escrow.amount,
                transaction_type=WalletTransaction.DEBIT,
                description=f"Funding Escrow for {escrow.tenancy.unit.name}",
                reference=f"ESC-FUND-{escrow.id.hex[:8]}" # unique ref
            )

            # 5. Transition the Escrow state using your model logic
            # This triggers your LifecycleMixin and Event logs
            escrow.fund(actor=actor)
            escrow.save()

            return escrow

    @staticmethod
    def release_escrow_to_landlord(escrow_id, actor):
        """
        Releases held funds from Escrow into the Organisation's Wallet.
        """
        with transaction.atomic():
            escrow = Escrow.objects.select_for_update().get(id=escrow_id)

            if escrow.status != Escrow.FUNDED:
                raise ValidationError("Only funded escrows can be released.")

            # Get or create the Organisation's wallet
            org_wallet, _ = Wallet.objects.get_or_create(
                organisation=escrow.organisation,
                defaults={'user': None}
            )

            # Create the Credit Transaction for the Landlord/Org
            WalletTransaction.objects.create(
                wallet=org_wallet,
                amount=escrow.amount,
                transaction_type=WalletTransaction.CREDIT,
                description=f"Escrow Payout: {escrow.tenancy.unit.name}",
                reference=f"ESC-REL-{escrow.id.hex[:8]}"
            )

            # Transition and record time
            escrow.release(actor=actor)
            escrow.released_at = transaction.now()
            escrow.save()

            return escrow