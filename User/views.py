from PIL import Image, UnidentifiedImageError
from django.core.files.uploadedfile import UploadedFile # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from constants import DEFAULT_ERROR  # type: ignore
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_delete,
    is_hx_get,
    is_hx_post,
    auth_needed,
    login_needed,
)
from User.models import get_user  # type: ignore
from Crypto.Random.random import randint
from Main.templatetags.bad_image import bad_image
from tools.utils import setSwalAlert


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


@htmx_response
@auth_needed()
def change_image(req: HttpRequest):
    if is_hx_post(req):
        user = get_user(req)
        context = {"profile": f"data:image/jpeg;base64,{bad_image}", **setSwalAlert(title="Profile Image Change")}

        try:
            role = user.role
            image: UploadedFile = req.FILES["image"]  # type: ignore

            with image.open() as f:
                Image.open(f)
                role.profile.save(f.name, f)  # type: ignore
            role.save()

            context["profile"] = role.profile.url  # type: ignore
            
            setSwalAlert(context, "Image Change was successful", "success")
        
        except UnidentifiedImageError:
            setSwalAlert(context, "Invalid Image Uploaded!"  )
            
        except Exception as e:
            setSwalAlert(context,  DEFAULT_ERROR)

        return render(req, "User/HTMX/image/image.html", context=context)
    
    if is_hx_delete(req):
        user = get_user(req)
        context = {"profile": f"data:image/jpeg;base64,{bad_image}", **setSwalAlert(title="Profile Image Delete")}

        try:
            role = user.role
            role.profile.delete(save=True)  # type: ignore

            if role.has_profile_image():
                context["profile"] = role.profile.url  # type: ignore
            else:
                context["profile"] = "/media/profile/default.profile.png"  # type: ignore
                
            setSwalAlert(context, "Image was deleted successful", "success")
        
        except Exception as e:
            setSwalAlert(context,  DEFAULT_ERROR)

        return render(req, "User/HTMX/image/image.html", context=context)
