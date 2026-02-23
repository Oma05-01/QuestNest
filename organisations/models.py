from django.db import models
from core.models import BaseModel
from django.conf import settings

class Organisation(BaseModel):
    name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def verified(self):
        return getattr(self, "verification", None) and self.verification.verified


class Workspace(BaseModel):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='workspaces'
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.organisation.name}"


class Membership(BaseModel):
    OWNER = "owner"
    MANAGER = "manager"
    OPERATOR = "operator"
    STAFF = "staff"
    TENANT = "tenant"

    ROLE_CHOICES = [
        (OWNER, "Owner"),
        (MANAGER, "Manager"),
        (OPERATOR, "Operator"),
        (STAFF, "Staff"),
        (TENANT, "Tenant"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="members"
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "organisation")

    def __str__(self):
        return f"{self.user.email} - {self.organisation.name} ({self.role})"
