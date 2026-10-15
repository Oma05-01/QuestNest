from django.db import models
from core.models import BaseModel
from django.conf import settings

class Workspace(BaseModel):
    PERSONAL = 'personal'
    BUSINESS = 'business'

    TYPE_CHOICES = [
        (PERSONAL, 'Personal'),
        (BUSINESS, 'Business'),
    ]

    name = models.CharField(max_length=255)
    workspace_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=BUSINESS)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_workspace_type_display()})"

    @property
    def verified(self):
        # Preserving your KYC verification logic!
        return getattr(self, "verification", None) and self.verification.verified


class Membership(BaseModel):
    OWNER = "owner"
    ADMIN = "admin"       # Added Admin for better team management
    MANAGER = "manager"
    MEMBER = "member"     # Replaced 'operator/staff' with standard SaaS terminology

    ROLE_CHOICES = [
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (MANAGER, "Manager"),
        (MEMBER, "Member"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="members"
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    is_active = models.BooleanField(default=True)

    class Meta:
        # A user can only have one active role per workspace
        unique_together = ("user", "workspace")

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"