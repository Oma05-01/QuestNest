import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')

# 1. Initialize the standard Django HTTP application early
django_asgi_app = get_asgi_application()

# 🟢 We import routing here to avoid "App Registry Not Ready" errors
import notifications.routing

application = ProtocolTypeRouter({
    # Handles standard HTTP requests (Tests 1-10)
    "http": django_asgi_app,
    
    # Handles real-time WebSocket requests (Phase 3)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications.routing.websocket_urlpatterns
        )
    ),
})