from django.urls import path  # type: ignore
from .views import (
    account_view,
)

app_name = "User"
urlpatterns = [
    path("", account_view, name="index"),
]
