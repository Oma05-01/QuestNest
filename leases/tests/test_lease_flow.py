import pytest
from leases.models import LeaseAgreement, LeaseSignature
from leases.services.lease_service import (
    create_lease_from_tenancy,
    send_lease_for_signature,
    sign_lease
)
from operations.models import Task
from payments.models import Payment


@pytest.mark.django_db
def test_end_to_end_lease_signing_flow(funded_tenant, landlord, active_tenancy):
    """
    Tests the golden path: A lease is generated, sent, signed by both parties,
    and successfully triggers background operations (tasks & payments).
    """

    # 1. Action: Generate the lease document
    lease = create_lease_from_tenancy(tenancy=active_tenancy, actor=landlord)
    assert lease.status == LeaseAgreement.DRAFT

    # 2. Action: Landlord sends it for signature
    send_lease_for_signature(lease=lease, actor=landlord)
    assert lease.status == LeaseAgreement.SENT

    # 3. Action: Tenant signs the lease
    sign_lease(lease=lease, user=funded_tenant, role=LeaseSignature.TENANT)
    lease.refresh_from_db()

    # State Check: Status should STILL be 'SENT' because the landlord hasn't signed!
    assert lease.status == LeaseAgreement.SENT

    # 4. Action: Landlord signs the lease (This triggers LEASE_SIGNED rules!)
    sign_lease(lease=lease, user=landlord, role=LeaseSignature.LANDLORD)
    lease.refresh_from_db()

    # --- ASSERTIONS ---

    # 1. The document should be legally binding
    assert lease.status == LeaseAgreement.SIGNED

    # 2. Background Rule: The move-in task should have been created for the staff
    assert Task.objects.filter(
        related_object_type="LeaseAgreement",
        related_object_id=str(lease.id),
        title="Prepare property for tenant move-in"
    ).exists()

    # 3. Background Rule: The first rent payment should be automatically initiated
    assert Payment.objects.filter(
        tenancy=active_tenancy,
        amount=lease.rent_amount,
        status=Payment.SUCCESS
    ).exists()