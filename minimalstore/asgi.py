import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import seller.routing  # Seller app routing
import user.routing    # User app routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimalstore.settings')

# Combine app-level WebSocket routes
websocket_urlpatterns = (
    seller.routing.websocket_urlpatterns + 
    user.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # ✅ Use the combined app routes
        )
    ),
})