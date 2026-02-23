from operations.models import Task


def create_task(
    *,
    organisation,
    title,
    description="",
    assigned_to=None,
    related_object_type=None,
    related_object_id=None,
    due_date=None
):
    return Task.objects.create(
        organisation=organisation,
        title=title,
        description=description,
        assigned_to=assigned_to,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        due_date=due_date
    )
