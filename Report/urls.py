from django.urls import path
from .views import *
from .sockets import CardWriteExeConsumer

app_name = "Report"
urlpatterns = [

    path("<str:id>/<int:idx>/", index_view, name="index"),
    path("<str:id>/<int:idx>/feed/", feed_view, name="feed"),
    path("<str:id>/<int:idx>/compress/", compress_view, name="compress"),
    path("<str:id>/<int:idx>/data/", card_view, name="data"),
    path("<str:id>/<int:idx>/<str:token>/fetch/", fetch_view, name="fetch"),
    path("<str:id>/<int:idx>/<str:token>/confirm/", issued_view, name="confirm"),
    path(
        "<str:id>/<int:idx>/<str:token>/",
        (lambda x: HttpResponse(status=404)),
        name="__base__",
    ),
]

websocket_urlpatterns = [
    path("view/<str:id>/<int:idx>/<str:token>/", CardWriteExeConsumer.as_asgi())
]
