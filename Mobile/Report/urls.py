from django.urls import path # type: ignore
from Mobile.Report.views import mobile_pdf_report, generate_report

app_name="Mobile-Report"
urlpatterns = [
    path("<str:cardID>", generate_report),
    path("pdf/<str:cardID>/<str:token>", mobile_pdf_report, name="mobilePDF"),
]
