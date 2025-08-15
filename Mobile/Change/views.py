from typing import Literal
from Mobile.types import CredResponse, OtpResponse, DeleteResponse
from User.errors import EmailAlreadyExists, OTPWrong, UserNameAlreadyExists
from django.http import HttpRequest, JsonResponse  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from constants import DEFAULT_ERROR
from Mobile.url_auth import (
    get_user_from_body,
    getRequestToken,
    is_auth_get_student,
    is_auth_post_student,
    jwt_required,
    read_body_as_json,
    student_auth_needed,
    set_otp_student_response,
    check_otp_student_response,
)
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from User.models import User, get_user
from Change.forms import (
    ForgotEmail,
    UsernameChange,
    PasswordChange,
    EmailChange,
    DeleteAccount,
)
from tools.mails import send_success_mail, send_delete_mail
from tools.url_auth import require_http_methods
from constants import OTP_MESSAGE, OTP_SUBJECT


def __nothing_to_see_here_trust_me__(req: HttpRequest):
    response = OtpResponse(status=False, error=[], **getRequestToken(req))
    status = 500
    send_ok = req.__getattribute__("emailOk")

    if send_ok:
        response["status"] = True
        status = 200
    else:
        response["error"] = ["Failed to send OTP"]

    return JsonResponse(data=response, status=status)


def __nothing_to_see_here__(req: HttpRequest):
    response = {"status": False, "error": []}
    status = 500
    send_ok = req.__getattribute__("emailOk")

    if send_ok:
        response["status"] = True
        status = 200
    else:
        response["error"] = ["Failed to send OTP"]

    return JsonResponse(data=response, status=status)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def send_otp_mail(req: HttpRequest, mailType: Literal["username", "email", "password"]):
    if is_auth_get_student(req):
        return set_otp_student_response(
            OTP_SUBJECT, OTP_MESSAGE, mailType.capitalize()
        )(__nothing_to_see_here_trust_me__)(req)

    elif is_auth_post_student(req):
        return set_otp_student_response(
            OTP_SUBJECT, OTP_MESSAGE, mailType.capitalize(), set_once=False
        )(__nothing_to_see_here_trust_me__)(req)


@csrf_exempt
@require_http_methods(['POST'])
@jwt_required  # type: ignore
@read_body_as_json
@get_user_from_body
@student_auth_needed
@check_otp_student_response
def password_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = PasswordChange(req.POST)
        response = CredResponse(status=False, error=[], **getRequestToken(req))
        status = 500

        if f.is_valid():
            try:
                password = str(f.cleaned_data.get("Password"))

                otpOk: bool = req.__getattribute__("ok")

                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.set_password(password)
                user.save()

                send_success_mail(req, "password")
                status = 200

            except OTPWrong as e:
                status = 401
                response["error"] = [e.get_error()]

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                response["error"] = [DEFAULT_ERROR]

        else:
            response["error"] = f.getJsonErrors()
            status = 400

        return JsonResponse(data=response, status=status)


@csrf_exempt
@require_http_methods(['POST'])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def email_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = EmailChange(req.POST)
        response = CredResponse(status=False, error=[], **getRequestToken(req))
        status = 500

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

                send_success_mail(req, "email")
                status = 200

            except OTPWrong as e:
                status = 401
                response["error"] = [e.get_error()]

            except EmailAlreadyExists as g:
                status = 403
                response["error"] = [g.get_error()]

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                response["error"] = [DEFAULT_ERROR]

        else:
            response["error"] = f.getJsonErrors()
            status = 400

        return JsonResponse(data=response, status=status)


@csrf_exempt
@require_http_methods(['POST'])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def username_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = UsernameChange(req.POST)
        response = CredResponse(status=False, error=[], **getRequestToken(req))
        status = 500

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

                send_success_mail(req, "username")
                status = 200

            except OTPWrong as e:
                status = 401
                response["error"] = [e.get_error()]

            except UserNameAlreadyExists as g:
                status = 403
                response["error"] = [g.get_error()]

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                response["error"] = [DEFAULT_ERROR]

        else:
            response["error"] = f.getJsonErrors()
            status = 400

        return JsonResponse(data=response, status=status)


@csrf_exempt
@require_http_methods(['POST'])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def delete_form(req: HttpRequest):
    if is_auth_post_student(req):
        response = DeleteResponse(status=False, error=[], **getRequestToken(req))
        f = DeleteAccount(req.POST)
        status = 500

        if f.is_valid():
            try:
                otpOk: bool = req.__getattribute__("ok")

                if not otpOk:
                    raise OTPWrong()

                user = get_user(req)

                user.delete()

                send_delete_mail(req)
                status = 200

            except OTPWrong as e:
                status = 401
                response["error"] = [e.get_error()]

            except Exception as e:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.EXCEPTION)
                    .set_meta(req)
                    .set_error(e)
                )
                response["error"] = [DEFAULT_ERROR]

        else:
            response["error"] = f.getJsonErrors()
            status = 400

        return JsonResponse(data=response, status=status)


@csrf_exempt
@require_http_methods(['POST'])
@read_body_as_json
def forgot_password(req: HttpRequest):
    if req.method == "POST":
        try:
            email = str(req.POST.get("Email"))

            user = User.objects.get(email=email)

            req.user = user

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )

        return set_otp_student_response(
            OTP_SUBJECT, OTP_MESSAGE, "password", set_once=False
        )(__nothing_to_see_here__)(req)
