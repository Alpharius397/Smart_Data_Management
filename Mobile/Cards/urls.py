from django.urls import path
from Mobile.Cards.views import (
    subscriber_check,
    available_card,
)

urlpatterns = [path("/status", subscriber_check), path("/", available_card)]
