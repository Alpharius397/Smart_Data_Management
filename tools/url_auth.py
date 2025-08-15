import typing
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from Main.models import RedisConnection, WriteToken, ReadToken, RedisDataBase, PdfToken
from Task.models import TaskTable
from constants import ACCESS_TOKEN, DEFAULT_ERROR, EMAIL_KEY, OTP_SIZE
from tools.encrypt import authTokenCheck
from User.models import (
    Role,
    User,
    ais_admin,
    ais_authenticated,
    ais_manager,
    get_user,
    is_admin,
    is_authenticated,
    is_manager,
)
from django.db.models import Q  # type: ignore
from Main.settings import settingsInterface as settings
from django.shortcuts import redirect  # type: ignore
from django.urls import reverse  # type: ignore
from University.models import Color
from functools import wraps
from tools.errors import TokenExpired
from Crypto.Random.random import randint
from asgiref.sync import sync_to_async
from tools.mails import email_send, validate_email  # type: ignore
from django.core.exceptions import ValidationError # type: ignore
from django.views.decorators.http import require_http_methods as _require_http_methods # type: ignore

REQUEST_PARAMS = typing.ParamSpec("REQUEST_PARAMS")


############ UTILS ############
def getOTP():
    return "".join(map(str, [randint(0, 9) for _ in range(OTP_SIZE)]))


def compareOTP(otp: str, verify: str):
    return otp == verify


def is_hx_get(req: HttpRequest) -> bool:
    return bool((req.method == "GET") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_get(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "GET")


def is_hx_post(req: HttpRequest) -> bool:
    return bool((req.method == "POST") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_post(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "POST")


def is_hx_put(req: HttpRequest) -> bool:
    return bool((req.method == "PUT") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_put(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "PUT")


def is_hx_delete(req: HttpRequest) -> bool:
    return bool((req.method == "DELETE") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_delete(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "DELETE")


def auth_page(req: HttpRequest) -> HttpResponse:
    return redirect(
        reverse(settings.LOGIN_URL)
        + f"?next={req.path}&warning=Unauthenticated Request!"
    )

def require_http_methods(request_method_list: list[typing.Literal['GET', 'POST', 'PUT', 'DELETE']]):
    return _require_http_methods(request_method_list) # type: ignore

def get_color(req: HttpRequest):
    try:
        user: User = get_user(req)
        role: Role = user.role
        color: Color = role.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        instituteIcon = color.instituteIcon.url
        req.session["mainColor"] = main_color
        req.session["secColor"] = sec_color
        req.session["instituteIcon"] = instituteIcon

        req.session["university_heading"] = role.belongs.institute.university.name
        req.session["institute_heading"] = role.belongs.institute.name
        req.session["branch_heading"] = role.belongs.name
    except Exception:
        pass


def taskCheck(user: User, id: int):
    try:
        if is_admin(user):
            return TaskTable.objects.get(Q(id=id) & Q(branch=user.role.belongs))

        elif is_manager(user):
            return TaskTable.objects.get(Q(id=id) & Q(assigned__manager__id=user.id))

    except Exception:
        pass

    return None


def semesterCheck(user: User, id: int, idx: int):
    try:
        if is_admin(user):
            return TaskTable.objects.filter(
                Q(id=id) & Q(data__semester=idx) & Q(branch=user.role.belongs)
            ).distinct()[0]

        elif is_manager(user):
            return TaskTable.objects.filter(
                Q(id=id) & Q(data__semester=idx) & Q(assigned__manager__id=user.id)
            ).distinct()[0]

    except Exception:
        pass

    return None


def login_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., HttpResponse | None],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            get_color(request)
            user = get_user(request)
            if is_authenticated(user):
                if not (manager_only or admin_only):  # both false
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(user)) or (
                    admin_only and is_admin(user)
                ):  # one of them is true
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return auth_page(request)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper


def auth_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users (HTMX Version)"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., HttpResponse | None],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            user = get_user(request)

            if is_authenticated(user):
                if not (manager_only or admin_only):  # both false
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(user)) or (
                    admin_only and is_admin(user)
                ):  # one of them is true
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return HttpResponse(status=403)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper


def media_access(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that need authenticated users using headers (Headless Chrome fix)"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            token = request.headers.get(ACCESS_TOKEN, "")

            if not token:
                raise Exception("Token Not Found")

            if request.user.is_authenticated:
                raise Exception("Skipping Auth Check")

            with RedisConnection(RedisDataBase.PDF_TOKEN) as redis:
                data: WriteToken | ReadToken | PdfToken = redis.getDict(token)  # type: ignore

                processing = data.get("processing", None)
                ID = data.get("ID", -1)

                if (not isinstance(processing, bool)) or (
                    isinstance(processing, bool) and (processing is not True)
                ):
                    raise TokenExpired()

                request.user = User.objects.get(id=ID)

        except Exception:
            pass

        user = get_user(request)

        if is_authenticated(user):
            return view_func(request, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view


def aauth_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users (HTMX Version)"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., typing.Awaitable[HttpResponse | None]],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        async def _wrapped_view(request: HttpRequest, *args, **kwargs):
            get_color(request)
            user = get_user(request)

            if await ais_authenticated(user):
                if not (manager_only or admin_only):  # both false
                    return await view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and (await ais_manager(user))) or (
                    admin_only and (await ais_admin(user))
                ):  # one of them is true
                    return await view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return HttpResponse(status=403)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper


def htmx_response(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that are HTMX response"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST"):
            return view_func(request, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view


def get_user_from_session(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that are session auth response"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            email = request.session.pop(EMAIL_KEY, None)
            if email is not None:
                request.user = User.objects.get(email=email)

        except Exception:
            pass

        return view_func(request, *args, **kwargs) or HttpResponse(status=403)

    return _wrapped_view


def set_otp_response(subject: str, message: str, type: str, set_once: bool = True):
    """Sets an `emailOk` denoting valid email address in request"""

    def __wrapper__(
        view_func: typing.Callable[..., HttpResponse | None],
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
                return view_func(request, *args, **kwargs) or HttpResponse(status=403)

            except ValidationError:
                request.__setattr__("emailOk", False)
                return view_func(request, *args, **kwargs) or HttpResponse(status=403)

            except Exception:
                return HttpResponse(status=403)

        return _wrapped_view

    return __wrapper__


def check_otp_response(
    view_func: typing.Callable[..., HttpResponse | None],
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

        return view_func(request, *args, **kwargs) or HttpResponse(status=403)

    return _wrapped_view


def task_permission_check(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that access tasks"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, id: int, *args, **kwargs):
        user = get_user(request)

        if (task := taskCheck(user, id)) != None:
            request.__setattr__("task", task)
            return view_func(request, id, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view


def async_task_permission_check(
    view_func: typing.Callable[..., typing.Awaitable[HttpResponse | None]],
) -> typing.Callable[..., typing.Awaitable[HttpResponse]]:
    @wraps(view_func)
    async def _wrapped_view(request: HttpRequest, id: int, *args, **kwargs):
        user = get_user(request)

        if (task := await sync_to_async(taskCheck)(user, id)) is not None:
            request.__setattr__("task", task)
            return (await view_func(request, id, *args, **kwargs)) or HttpResponse(
                status=403
            )

        return HttpResponse(status=403)

    return _wrapped_view


def semester_permission_check(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that access tasks"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, id: int, idx: int, *args, **kwargs):
        user = get_user(request)

        if (task := semesterCheck(user, id, idx)) is not None:
            request.__setattr__("task", task)
            return view_func(request, id, idx, *args, **kwargs) or HttpResponse(
                status=403
            )

        return HttpResponse(status=403)

    return _wrapped_view


def file_permission_check(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that access tasks"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, id: int, *args, **kwargs):
        user = get_user(request)

        if taskCheck(user, id):
            return view_func(request, id, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view


def api_key_required(view_func: typing.Callable[..., JsonResponse | None]):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization", "")

            if not auth_header.startswith("Bearer "):
                return JsonResponse(
                    {"error": "Authorization header missing or malformed"}, status=401
                )

            token = auth_header.split(" ")[1]
            if token and (authTokenCheck(token)):
                return view_func(request, *args, **kwargs) or JsonResponse(
                    {"error": "Invalid Request"}, status=403
                )
            else:
                return JsonResponse(
                    {"error": "Authorization Token is invalid"}, status=401
                )

        except Exception as e:
            APP_LOG.write_error(
                LogStructure().set_request(request, LogType.EXCEPTION).set_error(e)
            )
            return JsonResponse({"error": DEFAULT_ERROR}, status=404)

    return _wrapped_view


def pdf_access(view_func: typing.Callable[..., HttpResponse | None]):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            auth_header = request.headers.get("Access-PDF", "")

            if not (auth_header == settings.ACCESS_PDF):
                return HttpResponse(status=404)

            return view_func(request, *args, **kwargs) or HttpResponse(status=404)

        except Exception:
            return HttpResponse(status=404)

    return _wrapped_view


def token_check(database: RedisDataBase, close_after: bool = True):
    """Checks the token issuer and adds appropriate users for auth"""

    def __check__(view_func: typing.Callable[..., HttpResponse | None]):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            try:
                token = kwargs.get("token", "")
                with RedisConnection(database) as redis:
                    data: WriteToken | ReadToken | PdfToken = redis.getDict(token)  # type: ignore

                    processing = data.get("processing", None)
                    ID = data.get("ID", -1)

                    if (not isinstance(processing, bool)) or (
                        isinstance(processing, bool) and (processing is not True)
                    ):
                        raise TokenExpired()

                    request.user = User.objects.get(id=ID)
                    response = view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                    if close_after:
                        redis.unset(str(token))

                    return response

            except User.DoesNotExist:
                return HttpResponse(status=401)

            except Exception as e:
                APP_LOG.write_error(
                    LogStructure().set_request(request, LogType.EXCEPTION).set_error(e)
                )
                return HttpResponse(status=404)

        return _wrapped_view

    return __check__
