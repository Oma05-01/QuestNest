from django.db import models
from django.utils import timezone
from accounts.models import User
from properties.models import Property
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

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="tenancies"
    )

    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenancies"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant.email} - {self.property.name}"

    def activate(self, *, actor=None):
        self.transition_to(
            self.ACTIVE,
            actor=actor,
            event_type=EventType.TENANCY_ACTIVATED
        )