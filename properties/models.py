from django.db import models
from accounts.models import User
from django.db.models import Q
from organisations.models import Organisation
from operations.constants import EventType
from operations.services.event_service import log_event
from operations.rules import execute_rules
from operations.lifecycle import LifecycleMixin

class Property(LifecycleMixin, models.Model):
    DRAFT = "draft"
    LISTED = "listed"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    ARCHIVED = "archived"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (LISTED, "Listed"),
        (RESERVED, "Reserved"),
        (OCCUPIED, "Occupied"),
        (ARCHIVED, "Archived"),
    ]

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="self_properties", null=True, blank=True)
    name = models.CharField(max_length=255)
    location = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    saved_by = models.ManyToManyField(User, blank=True, related_name='saved_properties')

    def __str__(self):
        return self.name

    @property
    def is_available(self):
        from escrow.models import Escrow
        # Returns True if no active escrow
        active_escrows = self.escrows.filter(
            status__in=[Escrow.PENDING, Escrow.FUNDED]
        )
        return not active_escrows.exists()

    @property
    def is_verified(self):
        return getattr(self, "verification", None) and self.verification.verified


