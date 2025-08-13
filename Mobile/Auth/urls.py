from django.urls import path
from Mobile.Auth.views import (
    mobile_login,
    mobile_register,
    user_info,
    get_university,
    get_institute,
    get_branch,
)

urlpatterns = [
    path("user", user_info),
    path("login", mobile_login),
    path("register", mobile_register),
    path("university", get_university),
    path("institute", get_institute),
    path("branch", get_branch),
]
