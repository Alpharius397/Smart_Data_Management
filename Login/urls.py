from django.urls import path  # type: ignore
from .views import login_view, htmx_login_view

app_name = "Login"
urlpatterns = [
    path("", login_view, name="index"),  # type: ignore
    path("htmx", htmx_login_view, name="htmxLogin"),
]
