from typing import Literal
from django.urls import reverse  # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from User.errors import EmailAlreadyExists, OTPWrong, UserNameAlreadyExists
from Change.forms import (
    DeleteAccount,
    ForgotEmail,
    UsernameChange,
    PasswordChange,
    EmailChange,
)
from User.models import User, get_user
from tools.url_auth import (
    auth_needed,
    check_otp_response,
    get_user_from_session,
    htmx_response,
    is_auth_get,
    is_hx_post,
    is_hx_put,
    login_needed,
    read_body_as_form,
    set_otp_response,
)
from constants import (
    EMAIL_KEY,
    OTP_MESSAGE,
    OTP_SUBJECT,
    DEFAULT_ERROR,
)
from tools.utils import setSwalAlert
from tools.mails import send_success_mail, send_delete_mail, email_send
from django.contrib.auth import logout  # type: ignore
from tools.utils import SpecialHttpRequest


############ HTTP Request ############
@login_needed()
@set_otp_response(OTP_SUBJECT, OTP_MESSAGE, "Username")
def username_form(req: HttpRequest):
    
    emailOk = bool(req.__getattribute__("emailOk"))
    
    context = {"form": UsernameChange(), **setSwalAlert(title="OTP Mail")}
    
    if emailOk:
        setSwalAlert(context, text="OTP has been send to your email", icon="success")
    else:
        setSwalAlert(context, text="Failed to send OTP Mail")
    
    if is_auth_get(req):
        return render(
            req, "Change/HTML/username.html", context=context
        )


@login_needed()
@set_otp_response(OTP_SUBJECT, OTP_MESSAGE, "Username")
def email_form(req: HttpRequest):
    
    emailOk = bool(req.__getattribute__("emailOk"))
    
    context = {"form": EmailChange(), **setSwalAlert(title="OTP Mail")}
    
    if emailOk:
        setSwalAlert(context, text="OTP has been send to your email", icon="success")
    else:
        setSwalAlert(context, text="Failed to send OTP Mail")
        
    if is_auth_get(req):
        return render(req, "Change/HTML/email.html", context=context)


@get_user_from_session
@login_needed()
@set_otp_response(OTP_SUBJECT, OTP_MESSAGE, "Username")
def password_form(req: HttpRequest):
    
    emailOk = bool(req.__getattribute__("emailOk"))
    
    context = {"form": PasswordChange(), **setSwalAlert(title="OTP Mail")}
    
    if emailOk:
        setSwalAlert(context, text="OTP has been send to your email", icon="success")
    else:
        setSwalAlert(context, text="Failed to send OTP Mail")
        
    if is_auth_get(req):
        return render(
            req, "Change/HTML/password.html", context=context
        )


@login_needed()
@set_otp_response(OTP_SUBJECT, OTP_MESSAGE, "Account Deletion")
def delete_form(req: HttpRequest):

    
    emailOk = bool(req.__getattribute__("emailOk"))
    
    context = {"form": DeleteAccount(), **setSwalAlert(title="OTP Mail")}
    
    if emailOk:
        setSwalAlert(context, text="OTP has been send to your email", icon="success")
    else:
        setSwalAlert(context, text="Failed to send OTP Mail")
    
    
    if is_auth_get(req):
        return render(
            req, "Change/HTML/delete.html", context=context
        )


############ HTMX Request ############
@htmx_response
@auth_needed()
@check_otp_response
def htmx_username_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Username Change")
        f = UsernameChange(req.POST)

        if f.is_valid():
            try:
                username = str(f.cleaned_data.get("Username"))

                if User.objects.filter(username=username).exists():
                    raise UserNameAlreadyExists(username)

                otpOk: bool = req.__getattribute__("ok")

                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.username = username
                user.save()

                setSwalAlert(context, "Username was changed successfully", "success")
                send_success_mail(req, "username")
                context["redirect"] = req.build_absolute_uri(reverse("User:index"))
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except UserNameAlreadyExists as g:
                setSwalAlert(context, g.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@auth_needed()
@check_otp_response
def htmx_email_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Email Change")
        f = EmailChange(req.POST)

        if f.is_valid():
            try:
                email = str(f.cleaned_data.get("Email"))

                if User.objects.filter(email=email).exists():
                    raise EmailAlreadyExists(email)

                otpOk: bool = req.__getattribute__("ok")
                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.email = email
                user.save()
                setSwalAlert(context, "Email was changed successfully", "success")
                send_success_mail(req, "email")

                context["redirect"] = req.build_absolute_uri(reverse("User:index"))
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except EmailAlreadyExists as g:
                setSwalAlert(context, g.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@get_user_from_session
@auth_needed()
@check_otp_response
def htmx_password_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Password Change")
        f = PasswordChange(req.POST)

        if f.is_valid():
            try:
                password = f.cleaned_data.get("Password")

                otpOk: bool = req.__getattribute__("ok")
                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.set_password(password)
                user.save()
                setSwalAlert(context, "Password was changed successfully", "success")
                send_success_mail(req, "password")

                context["redirect"] = req.build_absolute_uri(reverse("User:index"))
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


def forgot_password(req: HttpRequest):
    if req.method == "GET":
        return render(
            req, "Change/HTML/forgot.password.html", context={"form": ForgotEmail()}
        )

@htmx_response
@read_body_as_form
@check_otp_response
def send_otp_mail_password(req: SpecialHttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="OTP Mail")
        otp = req.__getattribute__("otp")
        user = get_user(req)

        send_ok = False

        if otp:
            send_ok = email_send(
                OTP_SUBJECT.format("Password"),
                user.email,
                OTP_MESSAGE.format("Password", otp),
            )

        if send_ok:
            setSwalAlert(context, "OTP has been send to your email", "success")

        return render(req, "Change/HTMX/messages.html", context=context)

    elif is_hx_put(req):
        context = setSwalAlert(title="Email Status")

        f = ForgotEmail(req.PUT)

        if f.is_valid():
            try:
                email = f.cleaned_data.get("Email")

                user = User.objects.get(email=email)

                req.session[EMAIL_KEY] = user.email
                context["redirect"] = req.build_absolute_uri(
                    reverse("Change:passChange")
                )

                setSwalAlert(text="Email was found!", icon="success")

            except User.DoesNotExist:
                setSwalAlert(context, text="Email is not registered")

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, text=f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)


@htmx_response
@auth_needed()
@check_otp_response
def htmx_delete_form(req: HttpRequest):
    if is_hx_post(req):
        context = setSwalAlert(title="Username Change")
        f = DeleteAccount(req.POST)

        if f.is_valid():
            try:
                otpOk: bool = req.__getattribute__("ok")

                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.delete()

                setSwalAlert(context, "Account was successfully deleted", "success")
                send_delete_mail(req)
                logout(req)

            except OTPWrong as e:
                setSwalAlert(context, e.get_error())

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())

        return render(req, "Change/HTMX/messages.html", context=context)
