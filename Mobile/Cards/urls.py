from django.urls import path # type: ignore
from Mobile.Cards.views import (
    subscriber_check,
    available_card,
    get_heading
)

urlpatterns = [path("status", subscriber_check), path("", available_card), path("heading", get_heading)]
