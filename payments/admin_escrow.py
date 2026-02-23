from django.core.exceptions import ValidationError

from payments.permissions import require_admin
from payments.services.rent_flow import (
    release_rent_escrow,
    refund_rent_escrow
)

def admin_release_escrow(*, admin_user, escrow):
    """
    Admin-controlled escrow release.
    """

    require_admin(admin_user)

    if escrow.status != escrow.FUNDED:
        raise ValidationError("Only funded escrows can be released.")

    return release_rent_escrow(escrow=escrow)


def admin_refund_escrow(*, admin_user, escrow, reason=None):
    """
    Admin-controlled escrow refund.
    """

    require_admin(admin_user)

    if escrow.status != escrow.FUNDED:
        raise ValidationError("Only funded escrows can be refunded.")

    # (Optional) store refund reason later
    return refund_rent_escrow(escrow=escrow)
