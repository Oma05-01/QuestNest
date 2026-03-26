from user_messages.models import Message
from operations.services.event_service import log_event

def create_message(*, user, content):
    """
    Creates a new message and logs the event for the system.
    """
    message = Message.objects.create(
        user=user,
        content=content
    )

    log_event(
        organisation=None, # Messages in this model are platform-level, not org-level
        actor=user,
        event_type="MESSAGE_CREATED", # Make sure to add this to operations/constants.py
        object_type="Message",
        object_id=str(message.id)
    )

    return message