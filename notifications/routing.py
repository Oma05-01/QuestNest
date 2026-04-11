from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # The URL will be: ws://domain/ws/notifications/
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]