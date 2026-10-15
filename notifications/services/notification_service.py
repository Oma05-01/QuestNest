from django.core.mail import send_mail
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

def create_notification(
    *,
    user,
    workspace=None,  # 🟢 CHANGED: Replaced organisation
    title,
    message,
    notification_type="info",
    metadata=None
):
    from notifications.models import Notification

    metadata = metadata or {}

    # 🟢 CHANGED: Added workspace to the uniqueness check
    existing = Notification.objects.filter(
        user=user,
        workspace=workspace,
        title=title,
        metadata=metadata
    ).first()

    if existing:
        return existing

    return Notification.objects.create(
        user=user,
        workspace=workspace,  # 🟢 CHANGED
        title=title,
        message=message,
        notification_type=notification_type,
        metadata=metadata
    )


def trigger_notification(
        user,
        title,
        message,
        workspace=None,  # 🟢 CHANGED: Replaced organisation
        notification_type="info",
        send_email=True,
        send_sms=False,
        metadata=None
):
    # 1. Store in DB (The "Source of Truth")
    notification = create_notification(
        user=user,
        workspace=workspace, # 🟢 CHANGED: Removed the old getattr(user, 'organisation') fallback
        title=title,
        message=message,
        notification_type=notification_type,
        metadata=metadata
    )

    # 2. WebSocket Push (The "Failsafe" Real-Time Layer)
    try:
        channel_layer = get_channel_layer()
        group_name = f"user_{user.id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "message": {
                    "id": notification.id,
                    "workspace_id": str(workspace.id) if workspace else None, # 🟢 NEW: Tell the frontend the context!
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "metadata": notification.metadata,
                    "created_at": notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        )
    except Exception as e:
        logger.error(f"Real-time notification failed for user {user.id}: {e}")

    # 3. External Delivery: Email
    if send_email and user.email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Email failed to send to {user.email}: {e}")

    return notification