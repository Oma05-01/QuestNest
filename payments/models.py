from django.db import models
from accounts.models import User
from rentals.models import Tenancy
from escrow.models import Escrow
from operations.lifecycle import LifecycleMixin
from organisations.models import Organisation


class Payment(LifecycleMixin, models.Model):
    INITIATED = "initiated"
    SUCCESS = "success"
    FAILED = "failed"
    PROCESSING = "processing"

    STATUS_CHOICES = [
        (INITIATED, "Initiated"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (PROCESSING, "Processing"),
    ]

    ALLOWED_TRANSITIONS = {
        INITIATED: [PROCESSING, SUCCESS, FAILED],  # 🟢 Added SUCCESS here for instant wallet transfers
        PROCESSING: [SUCCESS, FAILED],  # Kept for future third-party card payments
        SUCCESS: [],
        FAILED: [],
    }

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="payments",
        blank=True
    )

    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenancy = models.ForeignKey(
        Tenancy,
        on_delete=models.CASCADE,
        related_name="payments", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    reference = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=INITIATED
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
