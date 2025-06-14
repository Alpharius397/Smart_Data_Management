from django.urls import path
from Report.views import *
from .sockets import CardWriteExeConsumer

app_name = "Report"
urlpatterns = [
    path("<int:id>/<int:idx>/<int:rowID>/", sem_view, name="semIndex"),
    
    path("htmx/<int:id>/<int:idx>/<int:rowID>/feed", sem_feed_view, name="htmxSemFeedBack"),
    path("htmx/<int:id>/<int:idx>/<int:rowID>/", sem_report_view, name="htmxSemIndex"),
    
    # path("<str:id>/<int:idx>/compress/", compress_view, name="compress"),
    # path("<str:id>/<int:idx>/data/", card_view, name="data"),
    # path("<str:id>/<int:idx>/<str:token>/fetch/", fetch_view, name="fetch"),
    # path("<str:id>/<int:idx>/<str:token>/confirm/", issued_view, name="confirm"),
    path(
        "<str:id>/<int:idx>/<str:token>/",
        (lambda x: HttpResponse(status=404)),
        name="__base__",
    ),
]

websocket_urlpatterns = [
    path("report/<str:id>/<int:idx>/<str:token>/", CardWriteExeConsumer.as_asgi())
]
