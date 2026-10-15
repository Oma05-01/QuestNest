from django.db import models
from django.conf import settings

from workspaces.models import Workspace # 🟢 Updated import


class Notification(models.Model):

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

    TYPE_CHOICES = [
        (INFO, "Info"),
        (SUCCESS, "Success"),
        (WARNING, "Warning"),
        (ERROR, "Error"),
    ]

    # 🟢 KEPT: Notifications pop up on a human's phone/screen
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    # 🟢 CHANGED: The operational context of the notification
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications" # Added for team activity feeds!
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    notification_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=INFO
    )

    is_read = models.BooleanField(default=False)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} → {self.user.email}"