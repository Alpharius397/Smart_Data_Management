from django.urls import path
from Dash.views import (
    dash_board,
    task_fetch,
    read_screen,
    read_view,
)
from django.http import HttpResponse  # type: ignore
from .sockets import CardReadExeConsumer

app_name = "Dash"
urlpatterns = [
    path("", dash_board, name="index"),
    path("task/", task_fetch, name="taskFetch"),
    path("read/", read_screen, name="read"),
    
    path("htmx/read/", read_view, name="card_read"),
    path("<str:token>/read/", (lambda _: HttpResponse(status=404)), name="__base__"),
]

websocket_urlpatterns = [path("dash/<str:token>/", CardReadExeConsumer.as_asgi())]  # type: ignore
