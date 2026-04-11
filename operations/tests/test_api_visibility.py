import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from organisations.models import Organisation, Membership
from accounts.models import User
from rentals.models import Tenancy
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
def test_cannot_pay_rent_for_tenancy_in_another_org(organisation, funded_tenant, active_tenancy):
    """
    Ensures Tenant A (Org 1) cannot trigger a payment for a Tenancy
    that belongs to Org 2.
    """
    # 1. SETUP: Create a second organization and its tenancy
    org_2 = Organisation.objects.create(name="Competitor Realty")
    victim_user = User.objects.create(email="victim@competitor.com", role='tenant')
    Membership.objects.create(user=victim_user, organisation=org_2, role="owner")

    # This tenancy belongs to Org 2
    victim_tenancy = Tenancy.objects.create(
        organisation=org_2,
        tenant=victim_user,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=365),
        status="active",
        rent_amount=Decimal("1000.00")
    )

    # 2. ACT: Log in as Tenant A (Org 1)
    client = APIClient()
    client.force_authenticate(user=funded_tenant)

    # 3. ATTACK: Try to pay for the victim's tenancy
    url = reverse('payments:pay-rent')  # 🟢 Correct namespaced URL
    data = {
        "tenancy": victim_tenancy.id,
        "amount": "1000.00"
    }
    response = client.post(url, data)

    # 4. ASSERT: Access must be denied
    # If the serializer is doing its job, this should be 400 or 403
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]