from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from tools.url_auth import (
    is_auth_get,
    login_needed,
    require_http_methods
)
from User.models import get_user  # type: ignore
from Crypto.Random.random import randint


############ HTTP Request ############
@require_http_methods(['GET'])
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


