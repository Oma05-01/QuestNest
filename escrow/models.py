# escrow/models.py
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

    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tenant_escrows'
    )
    landlord = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='landlord_escrows'
    )

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="organisation_escrows",
        null=True,
        blank=True
    )

    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE, null=True, blank=True)

    workspace = models.ForeignKey(
        "organisations.Workspace",
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

    # New fields for rent period tracking
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    metadata = models.JSONField(default=dict, blank=True)

    released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Escrow {self.id} - {self.tenancy.unit.name}"

    def save(self, *args, **kwargs):
        # 🟢 CHANGED: Safely check if tenancy actually exists before accessing .unit
        if not self.organisation_id and self.tenancy and self.tenancy.unit:
            self.organisation = self.tenancy.unit.asset.organisation
        super().save(*args, **kwargs)

    def fund(self, *, actor=None):
        """
        Transition escrow to FUNDED.

        No financial logic here.
        All side effects are handled by rules.
        """
        if self.status != self.PENDING:
            return self  # idempotent safety

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