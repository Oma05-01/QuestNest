import uuid
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError


class Wallet(models.Model):
    user = models.OneToOneField(
        "accounts.User",  # Using string to avoid circular imports
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance(self):
        from django.db.models import Sum
        # Ensure we return Decimal 0.00 instead of 0 for mathematical consistency
        credits = self.transactions.filter(
            transaction_type="credit"
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        debits = self.transactions.filter(
            transaction_type="debit"
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        return Decimal(credits) - Decimal(debits)

    def can_pay(self, amount):
        with transaction.atomic():
            _ = Wallet.objects.select_for_update().get(id=self.id)
            return self.balance >= Decimal(str(amount))

    def deposit(self, amount, reference=None, description="Deposit"):
        """Creates a credit transaction to increase balance."""
        from wallet.models import WalletTransaction

        return WalletTransaction.objects.create(
            wallet=self,
            amount=Decimal(str(amount)),
            transaction_type=WalletTransaction.CREDIT,
            reference=reference or f"DEP-{uuid.uuid4().hex[:8].upper()}",
            description=description
        )

    def withdraw(self, amount, reference=None, description="Withdrawal"):
        amount_dec = Decimal(str(amount))

        with transaction.atomic():
            # Lock the row before checking balance and creating the transaction
            _ = Wallet.objects.select_for_update().get(id=self.id)

            if self.balance < amount_dec:
                raise ValidationError(f"Insufficient funds. Available: {self.balance}")

            return WalletTransaction.objects.create(
                wallet=self,
                amount=amount_dec,
                transaction_type=WalletTransaction.DEBIT,
                reference=reference or f"WTH-{uuid.uuid4().hex[:8].upper()}",
                description=description
            )

class WalletTransaction(models.Model):

    CREDIT = "credit"
    DEBIT = "debit"

    TYPE_CHOICES = [
        (CREDIT, "Credit"),
        (DEBIT, "Debit"),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )

    reference = models.CharField(
        max_length=255,
        unique=True
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(amount=0),
                name="amount_not_zero"
            )
        ]
