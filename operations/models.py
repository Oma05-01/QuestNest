from django.db import models
from django.conf import settings
from workspaces.models import Workspace # 🟢 Updated import
from core.models import BaseModel
from .constants import EventType

class Event(BaseModel):
    # 🟢 CHANGED: Events happen within the context of a Workspace
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="events"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    parent_event = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_events"
    )

    event_type = models.CharField(max_length=100, db_index=True)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    metadata = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("processed", "Processed"),
            ("failed", "Failed"),
        ],
        db_index=True
    )

    def __str__(self):
        return f"{self.event_type} - {self.workspace.name}"

    @property
    def object(self):
        from operations.utils import get_object_from_event
        return get_object_from_event(self)


class Task(BaseModel):
    OPEN = "open"
    COMPLETED = "completed"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (COMPLETED, "Completed"),
    ]

    # 🟢 CHANGED: The task belongs to the Workspace...
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    # 🟢 KEPT: ...but is assigned to a specific human.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=OPEN
    )

    due_date = models.DateTimeField(null=True, blank=True)

    related_object_type = models.CharField(max_length=100, null=True, blank=True)
    related_object_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


class EventRule(BaseModel):
    """
    Defines what action should occur when a specific event is triggered.
    """
    event_type = models.CharField(
        max_length=100,
        choices=EventType.choices(),
        help_text="The event this rule responds to"
    )

    # 🟢 CHANGED: If null, it's a QuestNest global rule. If set, it's a custom PM rule.
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If null, applies globally"
    )

    action_type = models.CharField(
        max_length=50,
        choices=(
            ("CREATE_TASK", "Create Task"),
            ("SEND_EMAIL", "Send Email"),
        ),
        default="CREATE_TASK"
    )

    action_payload = models.JSONField(
        default=dict,
        help_text="Configuration for the action (e.g., {'title': '...', 'description': '...'})"
    )

    execution_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["execution_order"]

    def __str__(self):
        action_name = self.action_payload.get('title', self.action_type)
        return f"{self.event_type} → {action_name}"


class RuleExecution(models.Model):
    # This model remains unchanged because it only tracks execution status via Event!
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

    STATUS_CHOICES = [
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (SKIPPED, "Skipped"),
    ]

    event = models.ForeignKey(
        "operations.Event",
        on_delete=models.CASCADE,
        related_name="rule_executions"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUCCESS)
    error_message = models.TextField(null=True, blank=True)
    execution_time = models.FloatField(null=True, help_text="Time taken in seconds")

    rule_name = models.CharField(max_length=255)

    executed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, blank=True, null=True)

    class Meta:
        unique_together = ("event", "rule_name")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rule_name} on Event {self.event_id} - {self.status}"