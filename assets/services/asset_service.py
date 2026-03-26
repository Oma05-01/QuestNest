from assets.models import Assets
from operations.constants import EventType
from operations.services.event_service import log_event

def create_asset(*, owner, name, location, organisation=None):
    asset = Assets.objects.create(
        owner=owner,
        name=name,
        location=location,
        organisation=organisation,
        status=Assets.DRAFT
    )

    log_event(
        organisation=organisation,
        actor=owner,
        event_type=EventType.PROPERTY_CREATED,
        object_type="Assets",
        object_id=str(asset.id),
    )
    return asset