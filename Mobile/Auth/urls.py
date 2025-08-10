from django.urls import path
from Mobile.Auth.views import mobile_login, mobile_register, user_info

urlpatterns = [
    path("user", user_info),
    path("login", mobile_login),
    path("register", mobile_register),
]
