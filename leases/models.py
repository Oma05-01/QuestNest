from django.db import models
from operations.lifecycle import LifecycleMixin


class LeaseAgreement(LifecycleMixin, models.Model):
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    ACTIVE = "active"
    TERMINATED = "terminated"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (SENT, "Sent for signature"),
        (SIGNED, "Signed"),
        (ACTIVE, "Active"),
        (TERMINATED, "Terminated"),
    ]

    # 🟢 CHANGED: Points to Workspace.
    workspace = models.ForeignKey(
        "workspaces.Workspace",  # Using string to prevent circular imports
        on_delete=models.CASCADE,
        related_name="leases"
    )

    tenancy = models.OneToOneField(
        "rentals.Tenancy",
        on_delete=models.CASCADE,
        related_name="lease"
    )

    rent_amount = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lease for {self.tenancy}"

    def save(self, *args, **kwargs):
        # 🟢 ADDED: Automatically inherit the workspace from the tenancy
        if not self.workspace_id and self.tenancy:
            self.workspace = self.tenancy.workspace
        super().save(*args, **kwargs)


class LeaseSignature(models.Model):
    TENANT = "tenant"
    LANDLORD = "landlord"  # This just means "acting as landlord" for the signature

    ROLE_CHOICES = [
        (TENANT, "Tenant"),
        (LANDLORD, "Landlord"),
    ]

    lease = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="signatures"
    )

    # 🟢 KEPT: Humans sign documents, so this correctly points to the User
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    signed_name = models.CharField(max_length=255)
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.role} signature by {self.user.email}"


class LeaseDocument(models.Model):
    lease = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    file = models.FileField(upload_to="leases/")
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lease Document v{self.version}"


class LeaseAmendment(models.Model):
    lease = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="amendments"
    )
    description = models.TextField()
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


class LeaseClauseTemplate(models.Model):
    # 🟢 ADDED: Multi-tenant upgrade!
    # If null, it's a global platform template.
    # If set, it's a custom template belonging to a specific property manager.
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="clause_templates",
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    body = models.TextField()
    clause_type = models.CharField(max_length=50)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LeaseClauseInstance(models.Model):
    lease = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="clauses"
    )

    template = models.ForeignKey(
        LeaseClauseTemplate,
        on_delete=models.SET_NULL,
        null=True
    )

    body = models.TextField()
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"Clause for {self.lease}"