from django.urls import path  # type: ignore
from .views import (
    account_view,
    get_username,
    get_email,
    get_password,
    change_email,
    change_username,
    change_password,
    get_profile,
    change_image,
)

app_name = "User"
urlpatterns = [
    path("", account_view, name="index"),
    path("image/", get_profile, name="image"),
    path("username/", get_username, name="username"),
    path("email/", get_email, name="mail"),
    path("password/", get_password, name="password"),
    path("change/image/", change_image, name="imageChange"),
    path("change/username/", change_username, name="userChange"),
    path("change/email/", change_email, name="mailChange"),
    path("change/password/", change_password, name="passChange"),
]
