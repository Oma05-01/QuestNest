import pytest
from channels.testing import WebsocketCommunicator
from notifications.consumers import NotificationConsumer
from notifications.services.notification_service import trigger_notification
from asgiref.sync import sync_to_async


# 🛡️ 1. The Mock Auth Wrapper (For testing only)
class MockAuthMiddleware:
    def __init__(self, inner, user):
        self.inner = inner
        self.user = user

    async def __call__(self, scope, receive, send):
        # Inject our test user directly into the WebSocket scope
        scope["user"] = self.user
        return await self.inner(scope, receive, send)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_receives_notification_instantly(organisation, funded_tenant):
    """
    Ensures that when trigger_notification is called,
    the WebSocket client receives the data in real-time.
    """
    # 2. SETUP: Wrap the Consumer directly with our Mock Auth
    test_app = MockAuthMiddleware(NotificationConsumer.as_asgi(), user=funded_tenant)

    communicator = WebsocketCommunicator(test_app, "/ws/notifications/")

    connected, _ = await communicator.connect()
    assert connected, "WebSocket failed to connect"

    # 3. ACT: Trigger a notification (Simulating the Rule Engine)
    await sync_to_async(trigger_notification)(
        user=funded_tenant,
        title="Live Update",
        message="WebSockets are working!",
        notification_type="success"
    )

    # 4. ASSERT: Does the communicator "hear" the message?
    response = await communicator.receive_json_from()

    assert response["title"] == "Live Update"
    assert response["type"] == "success"
    assert "WebSockets are working!" in response["message"]

    # 5. CLEANUP
    await communicator.disconnect()