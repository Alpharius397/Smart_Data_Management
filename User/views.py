from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_get,
    auth_needed,
    login_needed,
)
from User.models import get_user  # type: ignore
from Crypto.Random.random import randint

############ HTTP Request ############
@login_needed()
def account_view(req: HttpRequest):
    if is_auth_get(req):
        user = get_user(req)

        context = {
            "username": user.username or "No Username",
            "email": user.email or "No email",
            "password": "*" * (randint(8, 20)),
            "branch": user.role.belongs.name,
            "institute": user.role.belongs.institute.name,
            "university": user.role.belongs.institute.university.name,
            "role": user.role.role,
        }

        return render(req, "User/index.html", context=context)


############ HTMX Request ############
@htmx_response
@auth_needed()
def get_username(req: HttpRequest):
    if is_hx_get(req):
        username = get_user(req).username
        return render(
            req, "User/HTMX/username/username.html", context={"username": username}
        )
    return None

@htmx_response
@auth_needed()
def get_email(req: HttpRequest):
    user = get_user(req)
    if is_hx_get(req):
        return render(req, "User/HTMX/email/email.html", context={"email": user.email})
    return None

@htmx_response
@auth_needed()
def get_password(req: HttpRequest):
    if is_hx_get(req):
        defaultPassword = "*" * randint(8, 20)
        return render(
            req,
            "User/HTMX/password/password.html",
            context={"password": defaultPassword},
        )

    return None

@htmx_response
@auth_needed()
def get_profile(req: HttpRequest):
    if is_hx_get(req):
        return render(req, "User/profile/profile.html")