from channels.auth import AuthMiddlewareStack, SessionMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Main.settings")
asgi = get_asgi_application()

import Report.urls
import Dash.urls

websocket_urlpatterns = [
    *Report.urls.websocket_urlpatterns,
    *Dash.urls.websocket_urlpatterns,
]

application = ProtocolTypeRouter(
    {
        "http": asgi,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
