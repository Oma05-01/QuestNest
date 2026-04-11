import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            # Create a unique group name for this user
            self.group_name = f"user_{self.user.id}"

            # Join the group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # 🟢 This method receives the signal and sends it to the frontend
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["message"]))