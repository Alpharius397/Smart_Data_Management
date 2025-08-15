import json
import typing
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict  # type: ignore
import jwt
from Logs.loggers import APP_LOG, LogStructure, LogType
from Main.models import RedisConnection, RedisDataBase
from constants import DEFAULT_ERROR
from User.models import User, get_user, is_authenticated_student
from functools import wraps
from django.utils import timezone  # type: ignore
from tools.mails import email_send, validate_email  # type: ignore
from django.core.exceptions import ValidationError # type: ignore
from tools.url_auth import getOTP, compareOTP
from Mobile.types import JwtToken, AccessPayLoad, RefreshPayLoad
from tools.utils import tryCatchThis


############ UTILS ############
def getRequestToken(req: HttpRequest):
    return JwtToken(
        access=tryCatchThis(req.headers.__getattribute__, "")("access"),
        refresh=tryCatchThis(req.headers.__getattribute__, "")("refresh"),
    )


def is_auth_get_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "GET")


def is_auth_post_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "POST")


def is_auth_put_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "PUT")


def is_auth_delete_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "DELETE")


def student_auth_needed(
    view_func: typing.Callable[..., JsonResponse | None],
):
    """Wrapper for views that need authenticated users (JSON Version)"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        if is_authenticated_student(get_user(request)):
            return view_func(request, *args, **kwargs) or JsonResponse(
                data={"error": DEFAULT_ERROR}, status=403
            )
        return JsonResponse(data={"error": DEFAULT_ERROR}, status=403)

    return _wrapped_view


def get_user_from_body(view_func: typing.Callable[..., JsonResponse | None]):
    def __inner__(req: HttpRequest, *args, **kwargs):
        try:
            email = str(req.__getattribute__(str(req.method)).get("Email"))

            user = User.objects.get(email=email)

            req.user = user

        except Exception:
            pass

        return view_func(req, *args, **kwargs) or JsonResponse(
            data={"error": DEFAULT_ERROR}, status=403
        )

    return __inner__


def set_otp_student_response(
    subject: str, message: str, type: str, set_once: bool = True
):
    """Sets an `emailOk` denoting valid email address in request"""

    def __wrapper__(
        view_func: typing.Callable[..., JsonResponse | None],
    ):
        """Wrapper for views that generates OTP"""

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            user = get_user(request)

            try:
                with RedisConnection(RedisDataBase.OTP_TOKEN) as redis:
                    otp = getOTP()

                    validate_email(user.email)

                    if not (redis.exists(str(user.id)) and set_once):
                        email_send.delay(
                            subject.format(type.capitalize()),
                            user.email,
                            message.format(type.capitalize(), otp),
                        )

                        redis.setText(str(user.id), otp, set_once=set_once)

                    request.__setattr__("emailOk", True)
                return view_func(request, *args, **kwargs) or JsonResponse(
                    data={"error": DEFAULT_ERROR}, status=403
                )

            except ValidationError:
                request.__setattr__("emailOk", False)
                return view_func(request, *args, **kwargs) or JsonResponse(
                    data={"error": DEFAULT_ERROR}, status=403
                )

            except Exception as e:
                APP_LOG.write_error(
                    LogStructure().set_request(request, LogType.EXCEPTION).set_error(e)
                )
                return JsonResponse(data={"error": DEFAULT_ERROR}, status=403)

        return _wrapped_view

    return __wrapper__


def check_otp_student_response(
    view_func: typing.Callable[..., JsonResponse | None],
):
    """Wrapper for views that makes uses of OTP (Note: request object gets a `otp` attr that has OTP and `ok` attr that checks if otp is ok)"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        request.__setattr__("otp", "Error sending OTP")
        request.__setattr__("ok", False)

        user = get_user(request)

        try:
            queryDict: QueryDict = request.__getattribute__(str(request.method))
            otp = queryDict.get("OTP", "######")

            with RedisConnection(RedisDataBase.OTP_TOKEN) as redis:
                verify = redis.getText(str(user.id))
                request.__setattr__("ok", compareOTP(verify, otp))
                request.__setattr__("otp", verify)

        except Exception:
            pass

        return view_func(request, *args, **kwargs) or JsonResponse(
            data={"error": DEFAULT_ERROR}, status=403
        )

    return _wrapped_view


def jwt_required(
    view_func: typing.Callable[..., JsonResponse | None],
):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> JsonResponse:
        auth_header = request.headers.get("Authorization", "")
        refresh_header = request.headers.get("Refresh", "")

        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header missing or malformed"}, status=401
            )

        if not refresh_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header missing or malformed"}, status=401
            )

        try:
            access, refresh = auth_header.split(" ")[1], refresh_header.split(" ")[1]

            access_payload = AccessPayLoad.decodeToken(AccessPayLoad, access)
            refresh_payload = RefreshPayLoad.decodeToken(RefreshPayLoad, refresh)

            if (
                access_payload.expire < timezone.now()
                and refresh_payload.expire < timezone.now()
            ):
                raise jwt.ExpiredSignatureError()

            if access_payload.userID != refresh_payload.userID:
                raise jwt.InvalidTokenError()

            new_Token = bool(access_payload.expire < timezone.now())

            access_token = access_payload.getToken(new_Token)
            refresh_token = refresh_payload.getToken(new_Token)

            user = User.objects.get(
                id=access_payload.userID, username=access_payload.username
            )

            request.user = user
            request.headers.__setattr__("access", access_token)
            request.headers.__setattr__("refresh", refresh_token)
            return view_func(request, *args, **kwargs) or JsonResponse(
                {"error": DEFAULT_ERROR}, status=403
            )

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)

        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        except Exception as e:
            APP_LOG.write_error(
                LogStructure().set_error(e).set_request(request, LogType.EXCEPTION)
            )
            return JsonResponse({"error": DEFAULT_ERROR}, status=500)

    return _wrapped_view


def read_body_as_json(view_func: typing.Callable[..., JsonResponse | None]):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            if request.method not in ["GET", "POST", "PUT", "DELETE"]:
                raise ValueError("Invalid Request Method")
            request.__setattr__(request.method, json.loads(request.body))
        except Exception:
            pass

        return view_func(request, *args, **kwargs) or JsonResponse(
            data={"error": DEFAULT_ERROR}, status=403
        )

    return _wrapped_view


def read_body_as_form(view_func: typing.Callable[..., JsonResponse | HttpResponse | None]):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            if request.method not in ["GET", "POST", "PUT", "DELETE"]:
                raise ValueError("Invalid Request Method")
            request.__setattr__(request.method, QueryDict(request.body))
        except Exception:
            pass

        return view_func(request, *args, **kwargs)

    return _wrapped_view
