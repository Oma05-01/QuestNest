from django.db import models
from accounts.models import User
from django.db.models import Sum

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Wallet"

    @property
    def balance(self):
        credits = self.transactions.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or 0

        debits = self.transactions.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or 0

        return credits - debits


class WalletTransaction(models.Model):
    CREDIT = 'credit'
    DEBIT = 'debit'

    TRANSACTION_TYPE_CHOICES = [
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)

    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.amount}"
