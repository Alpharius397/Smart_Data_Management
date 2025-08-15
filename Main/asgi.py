from channels.auth import AuthMiddlewareStack, SessionMiddleware # type: ignore
from channels.routing import ProtocolTypeRouter, URLRouter # type: ignore
from channels.security.websocket import AllowedHostsOriginValidator # type: ignore
from django.core.asgi import get_asgi_application # type: ignore
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Main.settings")
asgi = get_asgi_application()

import Card.urls

websocket_urlpatterns = [
    *Card.urls.websocket_urlpatterns,
]

application = ProtocolTypeRouter(
    {
        "http": asgi,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                SessionMiddleware(URLRouter(websocket_urlpatterns))
            )
        ),
    }
)
