from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from workspaces.models import Workspace  # 🟢 Updated import

User = get_user_model()


class Conversation(BaseModel):
    # 🟢 ADDED: The business context where this chat is taking place
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True
    )

    # 🟢 KEPT: The actual humans involved in the chat
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        context = f" in {self.workspace.name}" if self.workspace_id else ""
        return f"Conversation {self.id}{context}"


class Message(BaseModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    # 🟢 KEPT: Humans send messages
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # Oldest first, so chat flows top-to-bottom

    def __str__(self):
        return f"From {self.sender.email} at {self.created_at}"