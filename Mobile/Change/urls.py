from django.urls import path, re_path
from .views import (
    set_otp_response,
    username_form,
    email_form,
    password_form,
    delete_form,
)

urlpatterns = [
    re_path(
        r"^mail/(?P<type>(username|email|password))/otp/$",
        set_otp_response,
    ),
    path("username", username_form),
    path("password", password_form),
    path("email", email_form),
    path("delete", delete_form),
]
