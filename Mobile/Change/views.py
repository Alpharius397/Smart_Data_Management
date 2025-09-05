from typing import Literal
from Mobile.types import CredResponse, OtpResponse, DeleteResponse
from User.errors import EmailAlreadyExists, OTPWrong, UserNameAlreadyExists
from django.http import HttpRequest, JsonResponse  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from constants import DEFAULT_ERROR
from Mobile.url_auth import (
    get_user_from_body,
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
    UsernameChange,
    PasswordChange,
    EmailChange,
    DeleteAccount,
)
from tools.mails import send_success_mail, send_delete_mail
from tools.url_auth import require_http_methods
from constants import OTP_MESSAGE, OTP_SUBJECT


def getMailMsg(mailType: Literal["username", "email", "password", "delete"]):
    match mailType:
        case "username":
            return "Username"
        case "email":
            return "Email"
        case "password":
            return "Password"
        case "delete":
            return "Account Deletion"


def __nothing_to_see_here_trust_me__(req: HttpRequest):
    response = OtpResponse(status=False, error=[])
    status = 500
    send_ok = req.__getattribute__("emailOk")

    if send_ok:
        response["status"] = True
        status = 200
    else:
        response["error"] = ["Failed to send OTP"]

    return JsonResponse(data=response, status=status)


def __nothing_to_see_here__(req: HttpRequest):
    response = OtpResponse(status=False, error=[])
    status = 500
    send_ok = req.__getattribute__("emailOk")

    if send_ok:
        response["status"] = True
        status = 200
    else:
        response["error"] = ["Failed to send OTP"]

    return JsonResponse(data=response, status=status)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
def send_otp_mail(
    req: HttpRequest, mailType: Literal["username", "email", "password", "delete"]
):
    if is_auth_post_student(req):
        return set_otp_student_response(
            OTP_SUBJECT, OTP_MESSAGE, getMailMsg(mailType), set_once=False
        )(__nothing_to_see_here_trust_me__)(req)


@csrf_exempt
@require_http_methods(["POST"])
@read_body_as_json
def forgot_password(req: HttpRequest):
    if req.method == "POST":
        try:
            email = str(req.POST.get("Email"))
            user = User.objects.get(
                email=email
            )  # No need to validate has we validate it in set_otp

            req.user = user

        except User.DoesNotExist:
            return JsonResponse(
                data=OtpResponse(
                    status=False,
                    error=["Email is not registered"],
                ),
                status=400,
            )

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )

        return set_otp_student_response(
            OTP_SUBJECT, OTP_MESSAGE, getMailMsg("password"), set_once=False
        )(__nothing_to_see_here__)(req)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def password_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = PasswordChange(req.POST)
        response = CredResponse(status=False, error=[])
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
                response["status"] = True
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
@require_http_methods(["POST"])
@read_body_as_json
@get_user_from_body
@student_auth_needed
@check_otp_student_response
def forgot_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = PasswordChange(req.POST)
        response = CredResponse(status=False, error=[])
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
                response["status"] = True
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
@require_http_methods(["POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def email_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = EmailChange(req.POST)
        response = CredResponse(status=False, error=[])
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
                response["status"] = True
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
@require_http_methods(["POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def username_form(req: HttpRequest):
    if is_auth_post_student(req):
        f = UsernameChange(req.POST)
        response = CredResponse(status=False, error=[])
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
                response["status"] = True
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
@require_http_methods(["POST"])
@jwt_required  # type: ignore
@read_body_as_json
@student_auth_needed
@check_otp_student_response
def delete_form(req: HttpRequest):
    if is_auth_post_student(req):
        response = DeleteResponse(status=False, error=[])
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
                response["status"] = True
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
