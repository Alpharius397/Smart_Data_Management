from django.urls import path, re_path
from .views import (
    forgot_password,
    send_otp_mail,
    username_form,
    email_form,
    password_form,
    delete_form,
    forgot_form
)

urlpatterns = [
    re_path(
        r"^mail/(?P<mailType>(username|email|password|delete))$",
        send_otp_mail,
    ),
    path("username", username_form),
    path("password", password_form),
    path("email", email_form),
    path("delete", delete_form),
    path("forgot", forgot_password),
    path('reset', forgot_form)
]
