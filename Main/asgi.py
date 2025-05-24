import os
from channels.auth import AuthMiddlewareStack, SessionMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
import View.urls
import Dash.urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Main.settings")
websocket_urlpatterns = [*View.urls.websocket_urlpatterns, *Dash.urls.websocket_urlpatterns]

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)