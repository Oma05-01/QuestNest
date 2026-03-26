from django.db import models
from django.conf import settings

from organisations.models import Organisation


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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        null=True,
        blank=True
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
