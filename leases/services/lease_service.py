from leases.models import (
    LeaseAgreement,
    LeaseClauseTemplate,
    LeaseClauseInstance,
    LeaseSignature
)

from operations.services.event_service import log_event
from operations.constants import EventType


def create_lease_from_tenancy(tenancy, actor=None):
    """
    Create a lease agreement from a tenancy.
    """

    lease = LeaseAgreement.objects.create(
        organisation=tenancy.organisation,
        tenancy=tenancy,
        rent_amount=tenancy.rent_amount,
        deposit_amount=tenancy.deposit_amount,
        start_date=tenancy.start_date,
        end_date=tenancy.end_date,
    )

    attach_default_clauses(lease)

    log_event(
        organisation=tenancy.organisation,
        actor=actor,
        event_type=EventType.LEASE_CREATED,
        object_type="LeaseAgreement",
        object_id=str(lease.id),
        metadata={
            "tenancy_id": tenancy.id
        }
    )

    return lease


def attach_default_clauses(lease):
    """
    Attach default clauses to a lease.
    """

    templates = LeaseClauseTemplate.objects.all()

    order = 1

    for template in templates:

        LeaseClauseInstance.objects.create(
            lease=lease,
            template=template,
            body=template.body,
            order=order
        )

        order += 1


def send_lease_for_signature(lease, actor=None):

    lease.status = LeaseAgreement.SENT
    lease.save()

    log_event(
        organisation=lease.organisation,
        actor=actor,
        event_type=EventType.LEASE_SENT,
        object_type="LeaseAgreement",
        object_id=str(lease.id),
    )


def sign_lease(lease, user, role, request=None):

    ip_address = None

    if request:
        ip_address = request.META.get("REMOTE_ADDR")

    LeaseSignature.objects.create(
        lease=lease,
        user=user,
        role=role,
        signed_name=user.name,
        ip_address=ip_address
    )

    check_if_fully_signed(lease)


def check_if_fully_signed(lease):

    roles_signed = set(
        lease.signatures.values_list("role", flat=True)
    )

    if {"tenant", "landlord"} <= roles_signed:

        lease.status = LeaseAgreement.SIGNED
        lease.save()

        log_event(
            organisation=lease.organisation,
            actor=None,
            event_type=EventType.LEASE_SIGNED,
            object_type="LeaseAgreement",
            object_id=str(lease.id),
        )


def activate_lease(lease, actor=None):

    lease.status = LeaseAgreement.ACTIVE
    lease.save()

    log_event(
        organisation=lease.organisation,
        actor=actor,
        event_type=EventType.LEASE_ACTIVATED,
        object_type="LeaseAgreement",
        object_id=str(lease.id),
    )