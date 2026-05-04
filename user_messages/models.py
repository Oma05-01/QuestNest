from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel # Assuming you have this from earlier

User = get_user_model()

class Conversation(BaseModel):
    # A conversation is essentially a room with 2 or more people
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True) # Used to sort the Inbox

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id}"

class Message(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Oldest first, so chat flows top-to-bottom

    def __str__(self):
        return f"From {self.sender.email} at {self.created_at}"