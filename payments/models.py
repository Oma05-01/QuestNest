from django.db import models
from accounts.models import User
from rentals.models import Tenancy
from escrow.models import Escrow
from operations.lifecycle import LifecycleMixin
from workspaces.models import Workspace  # 🟢 Updated import


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
        INITIATED: [PROCESSING, SUCCESS, FAILED],
        PROCESSING: [SUCCESS, FAILED],
        SUCCESS: [],
        FAILED: [],
    }

    # 🟢 CHANGED: Replaced organisation with workspace
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,  # Allows personal wallet top-ups
        blank=True
    )

    retry_count = models.IntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)

    # 🟢 KEPT: The human pulling out their credit card or wallet
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    tenancy = models.ForeignKey(
        Tenancy,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    reference = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=INITIATED, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.user.email} | {self.reference} - {self.status}"

    def save(self, *args, **kwargs):
        # 🟢 ADDED: Automatically route rent payments to the landlord's workspace
        if not self.workspace_id and self.tenancy:
            self.workspace = self.tenancy.workspace
        super().save(*args, **kwargs)

    def change_status(self, new_status):
        """
        Safely transition payment states.
        Raises ValueError if the move is illegal.
        """
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")

        self.status = new_status
        self.save(update_fields=['status'])


class EscrowActionLog(models.Model):
    # 🟢 KEPT AS IS: Actions are performed by human Admins on an Escrow
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