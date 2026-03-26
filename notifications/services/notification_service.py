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