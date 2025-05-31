import random
from django.core.exceptions import ValidationError
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from constants.constants import DEFAULT_ERROR  # type: ignore
from django.db.models.expressions import Q  # type: ignore
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_get,
    is_hx_post,
    auth_needed,
    login_needed,
)
from User.models import User, get_user  # type: ignore
from django.contrib.auth.hashers import check_password  # type: ignore
from django.contrib import messages
from User.errors import PasswordMismatch, UserNameAlreadyExists, EmailAlreadyExists


############ HTTP Request ############
@login_needed()
def account_view(req: HttpRequest) -> HttpResponse | None:
    if is_auth_get(req):
        return render(req, "User/index.html")


############ HTMX Request ############
@htmx_response
@auth_needed()
def get_username(req: HttpRequest):
    if is_hx_get(req):
        username = get_user(req).username
        return render(
            req, "User/HTMX/username/username.html", context={"username": username}
        )


@htmx_response
@auth_needed()
def change_username(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)

    if is_hx_get(req):
        username = user.username
        return render(
            req,
            "User/HTMX/username/username.change.html",
            context={"username": username},
        )

    elif is_hx_post(req):
        username = req.POST.get("username", "")
        user_id = user.id
        previous_name = user.username
        context = {"username": previous_name}

        try:
            if User.objects.filter(Q(username=username) & ~Q(id=user_id)).exists():
                raise UserNameAlreadyExists(previous_name)

            user.username = username
            user.save()

            context["username"] = username
            messages.success(
                req, f"Username changed from {previous_name} to {username}"
            )

        except ValidationError as f:
            for message in f.messages:
                messages.error(req, message)

        except UserNameAlreadyExists as g:
            messages.error(req, g.get_error())

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)
            print(e)

        return render(req, "User/HTMX/username/username.html", context=context)


@htmx_response
@auth_needed()
def get_email(req: HttpRequest):
    user = get_user(req)
    if is_hx_get(req):
        return render(req, "User/HTMX/email/email.html", context={"email": user.email})


@htmx_response
@auth_needed()
def change_email(req: HttpRequest) -> HttpResponse:
    user = get_user(req)
    if is_hx_get(req):
        return render(
            req, "User/HTMX/email/email.change.html", context={"email": user.email}
        )

    elif is_hx_post(req):
        email = req.POST.get("email", "")
        user_id = user.id
        previous_email = user.email
        context = {"email": previous_email}

        try:
            if User.objects.filter(Q(email=email) & ~Q(id=user_id)).exists():
                raise EmailAlreadyExists(email)

            user.email = email
            user.save()

            context["email"] = email
            messages.success(req, f"Email changed from {previous_email} to {email}")

        except ValidationError as f:
            for message in f.messages:
                messages.error(req, message)

        except EmailAlreadyExists as g:
            messages.error(req, g.get_error())

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)
            print(e)

        return render(req, "User/HTMX/email/email.html", context=context)


@htmx_response
@auth_needed()
def get_password(req: HttpRequest):
    if is_hx_get(req):
        defaultPassword = "*" * random.randint(8, 20)
        return render(
            req,
            "User/HTMX/password/password.html",
            context={"password": defaultPassword},
        )


@htmx_response
@auth_needed()
def change_password(req: HttpRequest) -> HttpResponse:
    user = get_user(req)

    if is_hx_get(req):
        return render(req, "User/HTMX/password/password.change.html")

    if is_hx_post(req):
        prevPass = req.POST.get("previous", None)
        newPass = req.POST.get("new", None)

        try:
            if not check_password(prevPass, user.password):
                raise PasswordMismatch()

            user.set_password(newPass)
            user.save()

            messages.success(req, "Password was changed successfully")

        except ValidationError as f:
            for message in f.messages:
                messages.error(req, message)

        except PasswordMismatch as g:
            messages.error(req, g.get_error())

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)
            print(e)

        return render(req, "User/HTMX/password/password.html")
