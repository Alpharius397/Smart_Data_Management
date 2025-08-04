from django.http import HttpResponse # type: ignore
from django.urls import path # type: ignore
from .views import *

app_name = "Card"
urlpatterns = [
    path(
        "<int:id>/<str:idx>/<int:schema>/<str:token>/",
        (lambda x: HttpResponse(status=404)),
        name="writeBase",
    ),
    path(
        "<int:id>/<str:idx>/<int:schema>/<str:token>/fetch/",
        fetch_data,
        name="fetch",
    ),
    path(
        "<int:id>/<str:idx>/<int:schema>/<str:token>/confirm/",
        confirm_view,
        name="confirm",
    ),
    path(
        "<str:token>/read/",
        read_view,
        name="read",
    )
]

websocket_urlpatterns = [
    path("ws/write/<int:id>/<str:idx>/<str:token>/", CardWriteExeConsumer.as_asgi()),
    path("ws/read/<str:token>/", CardReadExeConsumer.as_asgi()),
]
