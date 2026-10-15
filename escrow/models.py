from django.db import models
from accounts.models import User
from django.utils import timezone
from operations.constants import EventType
from operations.lifecycle import LifecycleMixin
from rentals.models import Tenancy


class Escrow(LifecycleMixin, models.Model):
    PENDING = 'pending'
    FUNDED = 'funded'
    RELEASED = 'released'
    REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (FUNDED, 'Funded'),
        (RELEASED, 'Released'),
        (REFUNDED, 'Refunded'),
    ]

    ALLOWED_TRANSITIONS = {
        PENDING: [FUNDED],
        FUNDED: [RELEASED, REFUNDED],
        RELEASED: [],
        REFUNDED: [],
    }

    # 🟢 KEPT: The human paying the money
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tenant_escrows'
    )

    # 🟢 REMOVED 'landlord' and 'organisation' entirely!

    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE, null=True, blank=True)

    # 🟢 KEPT: The business receiving the money
    workspace = models.ForeignKey(
        "workspaces.Workspace",  # Using string to avoid circular imports
        on_delete=models.CASCADE,
        related_name="escrows",
        null=True,
        blank=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    metadata = models.JSONField(default=dict, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        # Safely handle string representation if tenancy isn't set yet
        unit_name = self.tenancy.unit.name if self.tenancy and self.tenancy.unit else "Unknown Unit"
        return f"Escrow {self.id} - {unit_name}"

    def save(self, *args, **kwargs):
        # 🟢 CHANGED: Auto-assign the workspace directly from the Tenancy
        if not self.workspace_id and self.tenancy:
            self.workspace = self.tenancy.workspace
        super().save(*args, **kwargs)

    def fund(self, *, actor=None):
        if self.status != self.PENDING:
            return self

        return self.transition_to(
            self.FUNDED,
            actor=actor,
            event_type=EventType.ESCROW_FUNDED,
        )

    def release(self, *, actor=None):
        if self.status != self.FUNDED:
            return self

        return self.transition_to(
            self.RELEASED,
            actor=actor,
            event_type=EventType.ESCROW_RELEASED
        )

    def refund(self, *, actor=None):
        if self.status != self.FUNDED:
            return self

        return self.transition_to(
            self.REFUNDED,
            actor=actor,
            event_type=EventType.ESCROW_REFUNDED
        )

    @property
    def unit(self):
        return self.tenancy.unit if self.tenancy else None