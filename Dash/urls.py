from django.urls import path
from Dash.views import (
    dash_board,
    admin_upload_fetch,
    admin_manage_fetch,
    manager_fetch,
    read_screen,
    read_view,
    get_read_data,
)
from django.http import HttpResponse  # type: ignore
from .sockets import CardReadExeConsumer

app_name = "Dash"
urlpatterns = [
    path("", dash_board, name="dash"),
    path("admin/uploader/", admin_upload_fetch, name="admin_upload"),
    path("admin/manager/", admin_manage_fetch, name="admin_manage"),
    path("manager/", manager_fetch, name="manage"),
    path("read/", read_screen, name="read"),
    path("read/operation/", read_view, name="card_read"),
    path("<str:token>/read/", get_read_data, name="read_url"),  # type: ignore
    path("<str:token>/", (lambda _: HttpResponse(status=404)), name="__base__"),
]

websocket_urlpatterns = [path("dash/<str:token>/", CardReadExeConsumer.as_asgi())]  # type: ignore
