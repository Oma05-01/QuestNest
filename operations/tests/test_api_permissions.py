import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestRolePermissions:

    def test_tenant_cannot_access_landlord_endpoints(self, funded_tenant):
        """
        Ensures a user with 'tenant' role is blocked from landlord-only views.
        """
        client = APIClient()
        client.force_authenticate(user=funded_tenant)  # Role is 'tenant'

        # 🟢 THE TARGET: A view that actually requires IsLandlord
        url = reverse('dashboards:landlord-dashboard')

        # ACT: Perform a GET (which this view supports)
        response = client.get(url)

        # ASSERT: Expect 403 Forbidden because the user is a Tenant
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_bypass_role_restrictions(self, organisation):
        """
        Ensures a user with 'admin' role can access tenant-restricted views.
        """
        from accounts.models import User
        from workspaces.models import Membership

        admin_user = User.objects.create(email="admin@questnest.com", role='admin', is_staff=True)
        Membership.objects.create(user=admin_user, organisation=organisation, role="owner")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        url = reverse('payments:pay-rent')
        response = client.post(url, {})  # Use POST to match the view

        # 🟢 Success: Admin is NOT forbidden
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_tenant_is_allowed_in_tenant_view(self, funded_tenant, active_tenancy):
        """
        Ensures a tenant CAN access their own view (405 is fine, 403 is NOT).
        """
        client = APIClient()
        client.force_authenticate(user=funded_tenant)
        url = reverse('payments:pay-rent')

        # We use POST here because PayRentView is a POST view
        # We don't care if the data is invalid (400), we just want to pass the 403 gate.
        response = client.post(url, {})

        assert response.status_code != status.HTTP_403_FORBIDDEN