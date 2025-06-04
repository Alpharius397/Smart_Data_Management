from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
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
from Crypto.Random.random import randint
from Main.templatetags.bad_image import bad_image


############ HTTP Request ############
@login_needed()
def account_view(req: HttpRequest) -> HttpResponse | None:
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
            "profile": user.role.profile.url,
        }

        try:
            with user.role.profile.open() as f:
                Image.open(f)

            context["profile"] = user.role.profile.url

        except Exception as e:
            print(e)
            messages.error(req, "Invalid Image")
            context["profile"] = f"data:image/jpeg;base64,{bad_image}"
        return render(req, "User/index.html", context=context)

    return None


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
    return None


@htmx_response
@auth_needed()
def get_email(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)
    if is_hx_get(req):
        return render(req, "User/HTMX/email/email.html", context={"email": user.email})
    return None


@htmx_response
@auth_needed()
def change_email(req: HttpRequest) -> HttpResponse | None:
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
    return None


@htmx_response
@auth_needed()
def get_password(req: HttpRequest) -> HttpResponse | None:
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
def change_password(req: HttpRequest) -> HttpResponse | None:
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
    return None


@htmx_response
@auth_needed()
def get_profile(req: HttpRequest) -> HttpResponse | None:
    if is_hx_get(req):
        return render(req, "User/profile/profile.html")
    return None


@htmx_response
@auth_needed()
def change_image(req: HttpRequest) -> HttpResponse | None:
    if is_hx_post(req):
        user = get_user(req)
        context = {"profile": f"data:image/jpeg;base64,{bad_image}"}

        try:
            role = user.role
            image: UploadedFile = req.FILES["image"]  # type: ignore

            with image.open() as f:
                Image.open(f)
                role.profile.save(f.name, f)  # type: ignore
            role.save()

            context["profile"] = role.profile.url  # type: ignore
            messages.success(req, "Image Change was successful")
        except Exception as e:
            messages.error(req, DEFAULT_ERROR)
            print(e)

        return render(req, "User/HTMX/image/image.html", context=context)
    return None
