from django.db import models
from django.conf import settings
from organisations.models import Organisation
from core.models import BaseModel
from django.apps import apps
from .constants import EventType

class Event(BaseModel):
    organisation = models.ForeignKey(
        Organisation,
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

    event_type = models.CharField(max_length=100)

    object_type = models.CharField(max_length=100)
    object_id = models.UUIDField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.event_type} - {self.organisation.name}"

    @property
    def object(self):
        model = apps.get_model(app_label=self.object_app, model_name=self.object_type)
        return model.objects.get(id=self.object_id)

class Task(BaseModel):
    OPEN = "open"
    COMPLETED = "completed"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (COMPLETED, "Completed"),
    ]

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

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
    related_object_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.title


class EventRule(BaseModel):
    """
    Defines what action should occur when a specific event is triggered.
    """

    event_type = models.CharField(
        max_length=100,
        choices=EventType.choices(),  # Assuming EventType has a choices method, or pass a list of tuples
        help_text="The event this rule responds to"
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If null, applies globally"
    )

    action_type = models.CharField(
        max_length=50,
        choices=(
            ("CREATE_TASK", "Create Task"),
            ("SEND_EMAIL", "Send Email"),  # Easy to add later!
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
        # Safely try to get a title if it exists in the JSON payload
        action_name = self.action_payload.get('title', self.action_type)
        return f"{self.event_type} → {action_name}"


class RuleExecution(models.Model):

    event = models.ForeignKey(
        "operations.Event",
        on_delete=models.CASCADE,
        related_name="rule_executions"
    )

    rule_name = models.CharField(max_length=255)

    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "rule_name")