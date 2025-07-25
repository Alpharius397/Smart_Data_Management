from django.urls import path  # type: ignore
from .views import (
    account_view,
    get_username,
    get_email,
    get_password,
    get_profile,
)

app_name = "User"
urlpatterns = [
    path("", account_view, name="index"),
    path("image/", get_profile, name="image"),
    path("username/", get_username, name="username"),
    path("email/", get_email, name="mail"),
    path("password/", get_password, name="password"),
]
