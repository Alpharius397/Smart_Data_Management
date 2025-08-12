from django.urls import path, re_path  # type: ignore
from .views import (
    delete_form,
    htmx_delete_form,
    username_form,
    email_form,
    password_form,
    forgot_password,
    htmx_username_form,
    htmx_email_form,
    htmx_password_form,
    send_otp_mail_password,
)

app_name = "Change"
urlpatterns = [
    path("username/", username_form, name="userChange"),
    path("email/", email_form, name="mailChange"),
    path("password/", password_form, name="passChange"),
    path("delete/", delete_form, name="delete"),
    path("forgotPassword/", forgot_password, name="forgotPassChange"),  # type: ignore
    path("htmx/username/", htmx_username_form, name="htmxUserChange"),
    path("htmx/email/", htmx_email_form, name="htmxEmailChange"),
    path("htmx/delete/", htmx_delete_form, name="htmxDelete"),
    path("htmx/password/", htmx_password_form, name="htmxPasswordChange"),
    path("htmx/forgotPassword", send_otp_mail_password, name="htmxForgotPassChange"),
]
