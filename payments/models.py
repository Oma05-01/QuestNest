from django.db import models
from accounts.models import User
from assets.models import Unit
from escrow.models import Escrow
from operations.lifecycle import LifecycleMixin
from organisations.models import Organisation


class Payment(LifecycleMixin, models.Model):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]

    ALLOWED_TRANSITIONS = {
        PENDING: [SUCCESS, FAILED],
        SUCCESS: [],
        FAILED: [],
    }

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="payments",
        blank=True
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE,
        null=True,
        blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.user.email} | {self.reference} - {self.status}"



class EscrowActionLog(models.Model):
    escrow = models.ForeignKey(
        Escrow,
        on_delete=models.CASCADE,
        related_name="admin_logs"
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(
        max_length=20,
        choices=(
            ("release", "Release"),
            ("refund", "Refund"),
        )
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} – Escrow #{self.escrow.id}"
