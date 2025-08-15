from django.urls import path  # type: ignore
from Report.views import (
    sem_view,
    index_view,
    generate_report,
    pdf_report,
    report_view,
    htmx_feedBack,
    issue_view,
    sem_feed_view,
    sem_report_view,
    htmx_schema,
)

app_name = "Report"
urlpatterns = [
    path("<int:id>/<int:idx>/<int:rowID>/", sem_view, name="semIndex"),
    path("<int:id>/<str:idx>", index_view, name="index"),
    path("<int:id>/<str:idx>/report", generate_report, name="report"),
    path("<int:id>/<str:idx>/<str:token>/pdf", pdf_report, name="pdf"),
    path("htmx/<int:id>/<str:idx>/", report_view, name="htmxIndex"),
    path("htmx/<int:id>/<str:idx>/feed/", htmx_feedBack, name="htmxFeed"),
    path("htmx/<int:id>/<str:idx>/issue", issue_view, name="htmxIssue"),
    path(
        "htmx/<int:id>/<int:idx>/<int:rowID>/feed",
        sem_feed_view,
        name="htmxSemFeedBack",
    ),
    path("htmx/<int:id>/<int:idx>/<int:rowID>/", sem_report_view, name="htmxSemIndex"),
    path("htmx/schema/", htmx_schema, name="htmxSchema"),
]
