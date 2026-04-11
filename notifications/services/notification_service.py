from django.core.mail import send_mail
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

def create_notification(
    *,
    user,
    organisation=None,
    title,
    message,
    notification_type="info",
    metadata=None
):
    from notifications.models import Notification

    metadata = metadata or {}

    existing = Notification.objects.filter(
        user=user,
        title=title,
        metadata=metadata
    ).first()

    if existing:
        return existing

    return Notification.objects.create(
        user=user,
        organisation=organisation,
        title=title,
        message=message,
        notification_type=notification_type,
        metadata=metadata
    )


def trigger_notification(
        user,
        title,
        message,
        organisation=None,
        notification_type="info",
        send_email=True,
        send_sms=False,
        metadata=None
):
    # 1. Store in DB (The "Source of Truth")
    notification = create_notification(
        user=user,
        organisation=organisation or getattr(user, 'organisation', None),
        title=title,
        message=message,
        notification_type=notification_type,
        metadata=metadata
    )

    # 2. WebSocket Push (The "Failsafe" Real-Time Layer) 🟢
    try:
        channel_layer = get_channel_layer()
        group_name = f"user_{user.id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",  # Matches consumer method
                "message": {
                    "id": notification.id,
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "created_at": notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        )
    except Exception as e:
        # 🛡️ GRACEFUL DEGRADATION:
        # If Redis is down, we log it but DON'T stop the function.
        # The user still gets their rent paid and the DB entry exists.
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
            # In production, log this to Sentry or similar
            print(f"Email failed: {e}")

    return notification