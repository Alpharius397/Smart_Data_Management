from django.urls import path, re_path # type: ignore
from .views import *

app_name = 'Change'
urlpatterns = [
    path("username/", username_form, name="userChange"),
    path("email/", email_form, name="mailChange"),
    path("password/", password_form, name="passChange"),
    
    path("htmx/username/", htmx_username_form, name="htmxUserChange"),
    path("htmx/email/", htmx_email_form, name="htmxEmailChange"),
    path("htmx/password/", htmx_password_form, name="htmxPasswordChange"),
    
    re_path(r"^mail/(?P<type>(username|email|password))/otp/$", send_otp_mail, name="otpSend"),
]
