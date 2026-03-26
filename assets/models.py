from django.db import models
from accounts.models import User
from organisations.models import Organisation
from operations.lifecycle import LifecycleMixin

class Assets(LifecycleMixin, models.Model):
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

    ALLOWED_TRANSITIONS = {
        DRAFT: [LISTED, ARCHIVED],
        LISTED: [RESERVED, ARCHIVED],
        RESERVED: [OCCUPIED, LISTED],
        OCCUPIED: [ARCHIVED],
        ARCHIVED: [],
    }

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="assets", null=True, blank=True)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_assets",
        blank=True,
        null=True
    )
    location = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    saved_by = models.ManyToManyField(User, blank=True, related_name='saved_assets')

    def __str__(self):
        return self.name

    @property
    def is_verified(self):
        return getattr(self, "verification", None) and self.verification.verified

class Unit(LifecycleMixin, models.Model):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

    ALLOWED_TRANSITIONS = {
        AVAILABLE: [RESERVED, OCCUPIED, MAINTENANCE],
        RESERVED: [OCCUPIED, AVAILABLE],
        OCCUPIED: [AVAILABLE, MAINTENANCE],
        MAINTENANCE: [AVAILABLE],
    }

    STATUS_CHOICES = [
        (AVAILABLE, "Available"),
        (RESERVED, "Reserved"),
        (OCCUPIED, "Occupied"),
        (MAINTENANCE, "Maintenance"),
    ]

    asset = models.ForeignKey(
        "Assets",
        on_delete=models.CASCADE,
        related_name="units"
    )

    name = models.CharField(max_length=100)  # e.g., "3B", "Room 204"

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AVAILABLE
    )

    rent_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.asset.name} - {self.name}"

    @property
    def organisation(self):
        return self.asset.organisation