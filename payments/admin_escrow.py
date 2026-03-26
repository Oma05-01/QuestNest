from django.core.exceptions import ValidationError

from payments.permissions import require_admin
from operations.services.event_service import log_event
from operations.constants import EventType


def admin_release_escrow(*, admin_user, escrow):
    """
    Admin triggers escrow release via event.
    """

    require_admin(admin_user)

    if escrow.status != escrow.FUNDED:
        raise ValidationError("Only funded escrows can be released.")

    log_event(
        organisation=escrow.organisation,
        actor=admin_user,
        event_type=EventType.ESCROW_RELEASE_REQUESTED,
        object_type="Escrow",
        object_id=str(escrow.id),
        metadata={
            "escrow_id": escrow.id
        }
    )


def admin_refund_escrow(*, admin_user, escrow, reason=None):
    """
    Admin triggers escrow refund via event.
    """

    require_admin(admin_user)

    if escrow.status != escrow.FUNDED:
        raise ValidationError("Only funded escrows can be refunded.")

    log_event(
        organisation=escrow.organisation,
        actor=admin_user,
        event_type=EventType.ESCROW_REFUND_REQUESTED,
        object_type="Escrow",
        object_id=str(escrow.id),
        metadata={
            "escrow_id": escrow.id,
            "reason": reason
        }
    )