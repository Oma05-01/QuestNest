import pytest
from django.urls import reverse
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from notifications.consumers import NotificationConsumer
from wallet.models import Wallet
from notifications.tests.test_websockets import MockAuthMiddleware


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestEndToEndWorkflows:

    async def test_tenant_pay_rent_complete_chain_reaction(self, organisation, funded_tenant, active_tenancy):
        """
        The Ultimate Domino Test:
        API Call -> Wallet Transfer -> Rule Fired -> Email Sent -> WebSocket Push.
        """
        # --- 1. SETUP: WebSocket Connection ---
        test_app = MockAuthMiddleware(NotificationConsumer.as_asgi(), user=funded_tenant)
        communicator = WebsocketCommunicator(test_app, "/ws/notifications/")
        connected, _ = await communicator.connect()
        assert connected

        wallet = await sync_to_async(Wallet.objects.get)(user=funded_tenant)
        start_balance = await sync_to_async(lambda: wallet.balance)()
        rent_to_pay = active_tenancy.rent_amount

        # --- 2. ACT: Tenant pays rent via the actual API ---
        client = APIClient()
        client.force_authenticate(user=funded_tenant)
        url = reverse('payments:pay-rent')

        # Simulating the frontend sending the tenancy_id
        payload = {
            "tenancy_id": active_tenancy.id,
            "amount": float(rent_to_pay)
        }
        response = await sync_to_async(client.post)(url, payload, format='json')

        # 🟢 Add this print to see the "why" in your terminal
        if response.status_code != 201:
            print(f"\n❌ Serializer Error: {response.data}")

        # --- 3. ASSERT: API & Wallet (Dominos 1 & 2) ---
        assert response.status_code == status.HTTP_201_CREATED

        # Refresh wallet from DB to see if money moved
        wallet = await sync_to_async(Wallet.objects.get)(user=funded_tenant)
        end_balance = await sync_to_async(lambda: wallet.balance)()

        # Math: Initial - Rent = Final
        assert end_balance == start_balance - rent_to_pay

        # --- 4. ASSERT: Email Dispatch (Domino 3) ---
        assert len(mail.outbox) >= 1
        assert "Payment Successful" in mail.outbox[0].subject

        # --- 5. ASSERT: WebSocket Real-Time Push (Domino 4) ---
        ws_message = await communicator.receive_json_from()
        assert ws_message["title"] == "Payment Successful!"
        assert ws_message["type"] == "success"

        # --- 6. CLEANUP ---
        await communicator.disconnect()

    async def test_pay_rent_idempotency_under_stress(self, funded_tenant, active_tenancy):
        """
        Simulates a user 'double-clicking' the pay button.
        The second request should not result in a second withdrawal.
        """
        client = APIClient()
        client.force_authenticate(user=funded_tenant)
        url = reverse('payments:pay-rent')
        payload = {
            "tenancy_id": active_tenancy.id,
            "amount": float(active_tenancy.rent_amount)
        }

        # 1. ACT: Fire two requests back-to-back
        # In a real stress test, we'd use asyncio.gather,
        # but even sequential rapid calls test your idempotency logic.
        response1 = await sync_to_async(client.post)(url, payload, format='json')
        response2 = await sync_to_async(client.post)(url, payload, format='json')

        # 2. ASSERT: First one is success, second one is handled gracefully
        assert response1.status_code == status.HTTP_201_CREATED

        # Depending on your logic, the 2nd should be 200 (OK) or 400 (Already Paid)
        # But it definitely should NOT be another 201 (Created)
        assert response2.status_code != status.HTTP_201_CREATED

        # 3. VERIFY: Only one set of transactions exists
        from wallet.models import WalletTransaction
        count = await sync_to_async(WalletTransaction.objects.filter(
            wallet__user=funded_tenant,
            amount=active_tenancy.rent_amount
        ).count)()

        assert count == 1, "User was double-charged!"