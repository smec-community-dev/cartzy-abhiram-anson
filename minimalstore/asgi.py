import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import minimalstore.routing  # Import project routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimalstore.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            minimalstore.routing.websocket_urlpatterns
        )
    ),
})