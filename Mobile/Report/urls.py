from django.urls import path
from Mobile.Report.views import (
    subscriber_check,
    available_card,
)

urlpatterns = [
    path("/", subscriber_check),
]
