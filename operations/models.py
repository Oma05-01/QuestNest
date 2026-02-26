from django.db import models
from django.conf import settings
from organisations.models import Organisation
from core.models import BaseModel
from django.apps import apps

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

    event_type = models.CharField(max_length=100, help_text="The event this rule responds to")

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
        ),
        default="CREATE_TASK",
        help_text="Type of action triggered by this rule"
    )

    task_title = models.CharField(max_length=255)
    task_description = models.TextField(blank=True)

    execution_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["execution_order"]

    def __str__(self):
        return f"{self.event_type} → {self.task_title}"
