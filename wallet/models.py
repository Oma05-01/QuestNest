import uuid
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError

from organisations.models import Organisation


class Wallet(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="wallet",
        null=True,  # 🟢 ADDED: DB must allow this to be empty!
        blank=True  # 🟢 ADDED: Forms must allow this to be empty!
    )

    organisation = models.OneToOneField(
        Organisation,
        on_delete=models.CASCADE,
        related_name='wallet',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.organisation_id:
            return f"{self.organisation.name}'s Wallet"
        return f"{self.user.email}'s Wallet"

    def clean(self):
        # 🟢 FIXED: Removed nested function and used _id consistently
        if self.user_id and self.organisation_id:
            raise ValidationError("A wallet cannot belong to both a user and an organisation.")

        if not self.user_id and not self.organisation_id:
            raise ValidationError("A wallet must belong to either a user or an organisation.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def balance(self):
        from django.db.models import Sum

        credits = self.transactions.filter(
            transaction_type=WalletTransaction.CREDIT  # 🟢 Minor fix: use the class constant
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        debits = self.transactions.filter(
            transaction_type=WalletTransaction.DEBIT  # 🟢 Minor fix: use the class constant
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        return Decimal(credits) - Decimal(debits)

    def can_pay(self, amount):
        with transaction.atomic():
            _ = Wallet.objects.select_for_update().get(id=self.id)
            return self.balance >= Decimal(str(amount))

    def deposit(self, amount, reference=None, description="Deposit"):

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

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} - ₦{self.amount} ({self.wallet})"

    class Meta:
        constraints = [
            # 🟢 FIXED: Amount must be strictly greater than zero to prevent negative debits
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="amount_must_be_positive"
            )
        ]