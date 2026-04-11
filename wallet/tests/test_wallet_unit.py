import pytest
from decimal import Decimal
from wallet.models import Wallet, WalletTransaction


@pytest.mark.django_db
class TestWalletCalculations:

    def test_new_wallet_has_zero_balance(self, user):
        """Ensure a wallet with no transactions returns 0, not None."""
        wallet = Wallet.objects.create(user=user)
        assert wallet.balance == 0

    def test_complex_ledger_calculation(self, wallet):
        """Test multiple credits and debits together."""
        WalletTransaction.objects.create(
            wallet=wallet, amount=Decimal("100.00"),
            transaction_type="credit", reference="REF1"
        )
        WalletTransaction.objects.create(
            wallet=wallet, amount=Decimal("250.00"),
            transaction_type="credit", reference="REF2"
        )
        WalletTransaction.objects.create(
            wallet=wallet, amount=Decimal("50.00"),
            transaction_type="debit", reference="REF3"
        )

        # 100 + 250 - 50 = 300
        assert wallet.balance == Decimal("300.00")

    def test_transaction_reference_uniqueness(self, wallet):
        """Ensure the database prevents double-entry with the same reference."""
        WalletTransaction.objects.create(
            wallet=wallet, amount=10, transaction_type="credit", reference="DUPE"
        )
        with pytest.raises(Exception):  # Specifically django.db.utils.IntegrityError
            WalletTransaction.objects.create(
                wallet=wallet, amount=10, transaction_type="credit", reference="DUPE"
            )