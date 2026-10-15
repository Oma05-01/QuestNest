from django.db import models
from core.models import BaseModel
from workspaces.models import Workspace  # 🟢 Updated import
from rentals.models import Unit


class MaintenanceRequest(BaseModel):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (LOW, 'Low'), (MEDIUM, 'Medium'), (HIGH, 'High'), (URGENT, 'Urgent'),
    ]

    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'

    STATUS_CHOICES = [
        (OPEN, 'Open'), (IN_PROGRESS, 'In Progress'),
        (RESOLVED, 'Resolved'), (CLOSED, 'Closed'),
    ]

    # 🟢 CHANGED: Replaced organisation entirely with workspace
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="maintenance_requests",
        null=True,
        blank=True
    )

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='maintenance_requests')

    # 🟢 KEPT: The human experiencing the issue
    tenant = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reported_issues')

    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)

    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.unit.name} ({self.status})"

    def save(self, *args, **kwargs):
        # 🟢 ADDED: Auto-assign the workspace based on the unit to prevent data leaks
        if not self.workspace_id and self.unit:
            self.workspace = self.unit.workspace
        super().save(*args, **kwargs)


class MaintenanceImage(BaseModel):
    request = models.ForeignKey(
        MaintenanceRequest,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='maintenance/requests/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.request.title}"


class Vendor(BaseModel):
    PLUMBING = 'plumbing'
    ELECTRICAL = 'electrical'
    CARPENTRY = 'carpentry'
    CLEANING = 'cleaning'
    GENERAL = 'general'

    CATEGORY_CHOICES = [
        (PLUMBING, 'Plumbing'), (ELECTRICAL, 'Electrical'),
        (CARPENTRY, 'Carpentry'), (CLEANING, 'Cleaning'), (GENERAL, 'General'),
    ]

    # 🟢 CHANGED: Vendors belong to a specific Property Management Workspace's rolodex
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="vendors"
    )

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=GENERAL)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"


class MaintenanceAssignment(BaseModel):
    request = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, related_name='assignments')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.vendor.name} assigned to {self.request.title}"


class MaintenanceComment(BaseModel):
    request = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    # 🟢 KEPT: Humans write comments.
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    body = models.TextField()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.request.title}"