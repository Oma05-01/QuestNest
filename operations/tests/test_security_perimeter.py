import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from rentals.models import Tenancy


@pytest.mark.django_db
class TestSecurityPerimeter:

    def test_cross_organisation_isolation_access_denied(self, organisation, funded_tenant, active_tenancy):
        """
        SECURITY: Tenant A should NOT be able to pay for Tenant B's house in another Org.
        """
        OrgModel = organisation.__class__
        UserModel = funded_tenant.__class__

        # 1. SETUP: Create Org B and their tenancy
        org_b = OrgModel.objects.create(name="Evil Corp", is_verified=True)
        tenant_b = UserModel.objects.create_user(
            email="evil@test.com",
            name="Evil Tenant",
            password="password",
            organisation=org_b
        )

        tenancy_b = Tenancy.objects.create(
            organisation=org_b,
            tenant=tenant_b,
            rent_amount=50000,
            status=Tenancy.ACTIVE,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365)
        )

        # 2. ACT: Tenant A tries to pay for Tenancy B
        client = APIClient()
        client.force_authenticate(user=funded_tenant)
        url = reverse('payments:pay-rent')

        payload = {"tenancy_id": tenancy_b.id, "amount": 50000}
        response = client.post(url, payload, format='json')

        # 3. ASSERT: 403 is the 'Bouncer' blocking the cross-org request
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_role_enforcement_landlord_cannot_pay_rent(self, organisation, active_tenancy):
        """
        RBAC: A 'Landlord' role should be blocked from the 'pay-rent' endpoint.
        """
        UserModel = active_tenancy.tenant.__class__
        landlord_user = UserModel.objects.create_user(
            email="joe@test.com",
            name="Landlord Joe",
            password="password",
            organisation=organisation,
            role='landlord'
        )

        client = APIClient()
        client.force_authenticate(user=landlord_user)
        url = reverse('payments:pay-rent')
        response = client.post(url, {"tenancy_id": active_tenancy.id, "amount": 1000})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unverified_organisation_blocked_from_payments(self, organisation, funded_tenant, active_tenancy):
        """
        KYC: Members of unverified organisations must be blocked from transactions.
        """
        # 1. SETUP: De-verify the org
        organisation.is_verified = False
        organisation.save()

        # 2. ACT
        client = APIClient()
        client.force_authenticate(user=funded_tenant)
        url = reverse('payments:pay-rent')
        response = client.post(url, {"tenancy_id": active_tenancy.id, "amount": 1000})

        # 3. ASSERT: Forbidden (Blocked by has_permission check)
        assert response.status_code == status.HTTP_403_FORBIDDEN