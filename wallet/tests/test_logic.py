import pytest
from django.core.exceptions import ValidationError
from wallet.models import Wallet


@pytest.mark.django_db
class TestWalletLogic:
    def test_deposit_increases_balance(self, wallet):
        initial = wallet.balance
        wallet.deposit(50000)
        assert wallet.balance == initial + 50000

    def test_withdraw_decreases_balance(self, wallet):
        wallet.deposit(100000)
        wallet.withdraw(40000)
        assert wallet.balance == 60000

    def test_negative_balance_protection(self, wallet):
        """Ensure users cannot spend more than they have."""
        wallet.deposit(1000)
        with pytest.raises(ValidationError):
            wallet.withdraw(5000)

        # Verify balance remains unchanged after failed withdrawal
        wallet.refresh_from_db()
        assert wallet.balance == 1000