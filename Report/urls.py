from django.urls import path
from Report.views import *
from .sockets import CardWriteExeConsumer

app_name = "Report"
urlpatterns = [
    path("<int:id>/<int:idx>/<int:rowID>/", sem_view, name="semIndex"),
    path("<int:id>/<str:idx>", index_view, name="index"),
    path("<int:id>/<str:idx>/report", generate_report, name="report"),
    path("htmx/<int:id>/<str:idx>/", report_view, name="htmxIndex"),
    path("htmx/<int:id>/<str:idx>/feed/", htmx_feedBack, name="htmxFeed"),
    path("htmx/<int:id>/<str:idx>/issue", issue_view, name="htmxIssue"),
    
    path("htmx/<int:id>/<int:idx>/<int:rowID>/feed", sem_feed_view, name="htmxSemFeedBack"),
    path("htmx/<int:id>/<int:idx>/<int:rowID>/", sem_report_view, name="htmxSemIndex"),
    path("htmx/schema/", htmx_schema, name="htmxSchema"),
    
    path(
        "<int:id>/<str:idx>/<str:token>/<int:schema>/",
        (lambda x: HttpResponse(status=404)),
        name="writeBase",
    ),
]

websocket_urlpatterns = [
    path("report/<str:id>/<int:idx>/<str:token>/", CardWriteExeConsumer.as_asgi())
]
