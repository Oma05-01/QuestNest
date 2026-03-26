from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.template.base import kwarg_re
from django.utils import timezone
from accounts.models import User
from assets.models import Unit
from organisations.models import Organisation
from operations.lifecycle import LifecycleMixin
from operations.constants import EventType


class Tenancy(LifecycleMixin, models.Model):

    PENDING = "pending"
    ACTIVE = "active"
    TERMINATED = "terminated"
    COMPLETED = "completed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (TERMINATED, "Terminated"),
        (COMPLETED, "Completed"),
    ]

    ALLOWED_TRANSITIONS = {
        PENDING: [ACTIVE, TERMINATED],
        ACTIVE: [COMPLETED, TERMINATED],
        TERMINATED: [],
        COMPLETED: [],
    }

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="tenancies"
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="unit_tenancies",
        null=True,
        blank=True
    )

    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenant_tenancies"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # deposit_amount might just be rent_amount
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    grace_period_days = models.IntegerField(default=3)

    rent_cycle_days = models.IntegerField(default=30, null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)

    late_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tenant.email} - {self.unit.name}"

    def clean(self):
        if self.unit.asset.organisation != self.organisation:
            raise ValidationError(
                "Unit does not belong to the specified organisation."
            )

    def save(self, *args, **kwarg):
        if not self.organisation_id and self.unit:
            self.organisation = self.unit.asset.organisation
        super().save(*args, **kwarg)

    def activate(self, *, actor=None):
        with transaction.atomic():
            self.transition_to(
                self.ACTIVE,
                actor=actor,
                event_type=EventType.TENANCY_ACTIVATED
            )